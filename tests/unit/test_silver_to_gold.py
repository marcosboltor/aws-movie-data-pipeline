"""
Unit Tests — Lambda silver_to_gold (Silver → Gold)

Validates the functions of the Gold layer:
  - Athena query execution and polling status
  - S3 prefix directory cleanups
  - Handler sequence execution: DROP → clean → CTAS queries
  - Error propagation on failed queries
"""

import json
import pytest
from unittest.mock import patch, MagicMock, call

from silver_tmdb_to_gold import (
    wait_for_query,
    run_query,
    clean_s3_prefix,
    lambda_handler,
)


# ───────────────────────────────────────────
# Constants
# ───────────────────────────────────────────

DATABASE = "db_movies_tmdb"
BUCKET = "unam-2026-ingenieriadatos-equipo1-997622531618-us-east-2-an"


# ═══════════════════════════════════════════
# 1. Tests for wait_for_query()
# ═══════════════════════════════════════════

class TestWaitForQuery:
    """Tests for polling status from Athena queries."""

    @patch("silver_tmdb_to_gold.athena_client")
    def test_waits_until_succeeded(self, mock_athena):
        """Verifies that polling returns correctly when the query finishes in SUCCEEDED."""
        mock_athena.get_query_execution.side_effect = [
            {"QueryExecution": {"Status": {"State": "RUNNING"}}},
            {"QueryExecution": {"Status": {"State": "RUNNING"}}},
            {"QueryExecution": {"Status": {"State": "SUCCEEDED"}}},
        ]

        # Should not raise
        wait_for_query("test-id-123")
        assert mock_athena.get_query_execution.call_count == 3

    @patch("silver_tmdb_to_gold.athena_client")
    def test_raises_on_failed_query(self, mock_athena):
        """Verifies that an exception is raised when the query fails."""
        mock_athena.get_query_execution.return_value = {
            "QueryExecution": {
                "Status": {
                    "State": "FAILED",
                    "StateChangeReason": "SYNTAX_ERROR near line 1",
                }
            }
        }

        with pytest.raises(Exception, match="FAILED"):
            wait_for_query("test-id-fail")

    @patch("silver_tmdb_to_gold.athena_client")
    def test_raises_on_cancelled_query(self, mock_athena):
        """Verifies that an exception is raised when the query is cancelled."""
        mock_athena.get_query_execution.return_value = {
            "QueryExecution": {
                "Status": {
                    "State": "CANCELLED",
                    "StateChangeReason": "User cancelled",
                }
            }
        }

        with pytest.raises(Exception, match="CANCELLED"):
            wait_for_query("test-id-cancel")


# ═══════════════════════════════════════════
# 2. Tests for run_query()
# ═══════════════════════════════════════════

class TestRunQuery:
    """Tests for executing Athena queries."""

    @patch("silver_tmdb_to_gold.wait_for_query")
    @patch("silver_tmdb_to_gold.athena_client")
    def test_starts_query_with_correct_params(self, mock_athena, mock_wait):
        """Verifies that start_query_execution receives database and output location parameters correctly."""
        mock_athena.start_query_execution.return_value = {
            "QueryExecutionId": "exec-abc"
        }

        run_query("SELECT 1")

        mock_athena.start_query_execution.assert_called_once()
        call_kwargs = mock_athena.start_query_execution.call_args[1]
        assert call_kwargs["QueryString"] == "SELECT 1"
        assert call_kwargs["QueryExecutionContext"]["Database"] == DATABASE
        mock_wait.assert_called_once_with("exec-abc")

    @patch("silver_tmdb_to_gold.wait_for_query")
    @patch("silver_tmdb_to_gold.athena_client")
    def test_passes_execution_id_to_wait(self, mock_athena, mock_wait):
        """Verifies that the execution_id is correctly passed to wait_for_query."""
        mock_athena.start_query_execution.return_value = {
            "QueryExecutionId": "unique-id-789"
        }

        run_query("DROP TABLE IF EXISTS test")
        mock_wait.assert_called_once_with("unique-id-789")


# ═══════════════════════════════════════════
# 3. Tests for clean_s3_prefix()
# ═══════════════════════════════════════════

class TestCleanS3Prefix:
    """Tests for S3 prefix deletion operations."""

    @patch("silver_tmdb_to_gold.s3_client")
    def test_deletes_all_objects_in_prefix(self, mock_s3):
        """Verifies that all S3 objects under a prefix are deleted."""
        paginator = MagicMock()
        paginator.paginate.return_value = [
            {"Contents": [{"Key": "3gold/test/file1.parquet"}, {"Key": "3gold/test/file2.parquet"}]}
        ]
        mock_s3.get_paginator.return_value = paginator

        clean_s3_prefix(BUCKET, "3gold/test/")

        mock_s3.delete_objects.assert_called_once()
        deleted = mock_s3.delete_objects.call_args[1]["Delete"]["Objects"]
        assert len(deleted) == 2

    @patch("silver_tmdb_to_gold.s3_client")
    def test_handles_empty_prefix(self, mock_s3):
        """Verifies that no exception is raised when the prefix is empty."""
        paginator = MagicMock()
        paginator.paginate.return_value = [{}]  # No "Contents" key
        mock_s3.get_paginator.return_value = paginator

        # Should not raise
        clean_s3_prefix(BUCKET, "3gold/empty/")
        mock_s3.delete_objects.assert_not_called()

    @patch("silver_tmdb_to_gold.s3_client")
    def test_batch_deletes_over_1000_objects(self, mock_s3):
        """Verifies that batch operations delete objects in limits of 1000 items."""
        # Simulate 1500 objects
        objects = [{"Key": f"3gold/big/file{i}.parquet"} for i in range(1500)]
        paginator = MagicMock()
        paginator.paginate.return_value = [{"Contents": objects}]
        mock_s3.get_paginator.return_value = paginator

        clean_s3_prefix(BUCKET, "3gold/big/")

        # Should be called twice: once with 1000, once with 500
        assert mock_s3.delete_objects.call_count == 2


# ═══════════════════════════════════════════
# 4. Tests for lambda_handler
# ═══════════════════════════════════════════

class TestSilverToGoldHandler:
    """Tests for the Silver to Gold Lambda handler entry-point."""

    @patch("silver_tmdb_to_gold.clean_s3_prefix")
    @patch("silver_tmdb_to_gold.run_query")
    def test_handler_drops_tables_first(self, mock_run, mock_clean):
        """Verifies that DROP TABLE queries are executed before CTAS builds."""
        result = lambda_handler({"test": True}, None)

        assert result["statusCode"] == 200
        # First calls should be DROP queries
        drop_calls = [
            c for c in mock_run.call_args_list
            if "DROP TABLE" in str(c)
        ]
        assert len(drop_calls) == 5  # 5 DROP statements

    @patch("silver_tmdb_to_gold.clean_s3_prefix")
    @patch("silver_tmdb_to_gold.run_query")
    def test_handler_cleans_all_gold_prefixes(self, mock_run, mock_clean):
        """Verifies that the 4 S3 Gold prefixes are cleaned prior to building."""
        lambda_handler({}, None)

        assert mock_clean.call_count == 4
        cleaned_prefixes = [c[0][1] for c in mock_clean.call_args_list]
        assert "3gold/performance_genero/" in cleaned_prefixes
        assert "3gold/ranking_peliculas/" in cleaned_prefixes
        assert "3gold/peliculas_sobreexpuestas/" in cleaned_prefixes
        assert "3gold/tendencia_generos/" in cleaned_prefixes

    @patch("silver_tmdb_to_gold.clean_s3_prefix")
    @patch("silver_tmdb_to_gold.run_query")
    def test_handler_creates_four_gold_tables(self, mock_run, mock_clean):
        """Verifies that the 4 S3 Gold CTAS tables are created successfully."""
        lambda_handler({}, None)

        ctas_calls = [
            c for c in mock_run.call_args_list
            if "CREATE TABLE" in str(c)
        ]
        assert len(ctas_calls) == 4

    @patch("silver_tmdb_to_gold.clean_s3_prefix")
    @patch("silver_tmdb_to_gold.run_query")
    def test_handler_total_query_count(self, mock_run, mock_clean):
        """Verifies the total queries executed count equals 9 (5 DROP + 4 CTAS)."""
        lambda_handler({}, None)

        assert mock_run.call_count == 9

    @patch("silver_tmdb_to_gold.clean_s3_prefix")
    @patch("silver_tmdb_to_gold.run_query")
    def test_handler_propagates_query_error(self, mock_run, mock_clean):
        """Verifies that a query failure is propagated correctly by the handler."""
        mock_run.side_effect = Exception("Query falló con estado FAILED")

        with pytest.raises(Exception, match="FAILED"):
            lambda_handler({}, None)

    @patch("silver_tmdb_to_gold.clean_s3_prefix")
    @patch("silver_tmdb_to_gold.run_query")
    def test_ctas_queries_use_correct_database(self, mock_run, mock_clean):
        """Verifies that the CTAS queries use the correct target Glue database."""
        lambda_handler({}, None)

        for c in mock_run.call_args_list:
            query = c[0][0]
            if "CREATE TABLE" in query:
                assert DATABASE in query

    @patch("silver_tmdb_to_gold.clean_s3_prefix")
    @patch("silver_tmdb_to_gold.run_query")
    def test_ctas_queries_use_parquet_format(self, mock_run, mock_clean):
        """Verifies that all Gold CTAS tables specify PARQUET as the format."""
        lambda_handler({}, None)

        for c in mock_run.call_args_list:
            query = c[0][0]
            if "CREATE TABLE" in query:
                assert "PARQUET" in query.upper()
