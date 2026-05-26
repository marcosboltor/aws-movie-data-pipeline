"""
Unit Tests — Lambda bronze_to_silver (Bronze → Silver)

Validates the transformation and data quality functions:
  - NDJSON loading from S3
  - Data cleaning (genre mapping, dates, audience_score)
  - Quality filters (vote_count ≥ 100, duplicate checking, null checking)
  - Silver Parquet generation
  - Downstream Gold Lambda invocation
  - S3 event handling and prefix matching logic
"""

import json
import boto3
import pytest
import pandas as pd
from datetime import datetime
from unittest.mock import patch, MagicMock

from bronce_tmdb_to_silver import (
    load_bronze_data,
    clean_data,
    apply_data_quality,
    invoke_gold_lambda,
    lambda_handler,
)


# ───────────────────────────────────────────
# Helpers
# ───────────────────────────────────────────

def _raw_df(overrides=None):
    """Generates a DataFrame simulating loaded Bronze data."""
    base = {
        "id": [100, 200, 300],
        "title": ["Alpha", "Beta", "Gamma"],
        "original_title": ["Alpha", "Beta", "Gamma"],
        "release_date": ["2026-01-15", "2025-11-20", "2026-03-10"],
        "original_language": ["en", "es", "en"],
        "genre_ids": [[28, 12], [18, 35], [27, 53]],
        "popularity": [150.5, 45.2, 200.0],
        "vote_average": [7.8, 6.1, 5.5],
        "vote_count": [1200, 350, 80],
        "adult": [False, False, False],
        "overview": ["Action adventure", "Dramatic comedy", "Horror thriller"],
        "source_page": [1, 1, 1],
        "ingestion_timestamp": ["2026-05-01T12:00:00"] * 3,
    }
    if overrides:
        base.update(overrides)
    return pd.DataFrame(base)


# ═══════════════════════════════════════════
# 1. Tests for load_bronze_data()
# ═══════════════════════════════════════════

class TestLoadBronzeData:
    """Tests for loading NDJSON data from S3."""

    def test_load_parses_ndjson_correctly(self, s3_with_bronze_file):
        """Verifies that multi-line NDJSON is correctly loaded and parsed."""
        bucket, key = s3_with_bronze_file

        with patch("bronce_tmdb_to_silver.s3") as mock_s3:
            real_s3 = boto3.client("s3", region_name="us-east-2")
            mock_s3.get_object = real_s3.get_object

            df = load_bronze_data(bucket, key)

        assert len(df) == 3
        assert "id" in df.columns
        assert "title" in df.columns

    def test_load_handles_trailing_commas(self):
        """Verifies that trailing commas at the end of NDJSON lines are handled correctly."""
        body = '{"id": 1, "title": "A"},\n{"id": 2, "title": "B"}\n'
        mock_response = {
            "Body": MagicMock(read=MagicMock(return_value=body.encode("utf-8")))
        }

        with patch("bronce_tmdb_to_silver.s3") as mock_s3:
            mock_s3.get_object.return_value = mock_response
            df = load_bronze_data("bucket", "key")

        assert len(df) == 2

    def test_load_skips_empty_lines(self):
        """Verifies that empty lines in the NDJSON body are skipped."""
        body = '{"id": 1}\n\n\n{"id": 2}\n\n'
        mock_response = {
            "Body": MagicMock(read=MagicMock(return_value=body.encode("utf-8")))
        }

        with patch("bronce_tmdb_to_silver.s3") as mock_s3:
            mock_s3.get_object.return_value = mock_response
            df = load_bronze_data("bucket", "key")

        assert len(df) == 2


# ═══════════════════════════════════════════
# 2. Tests for clean_data()
# ═══════════════════════════════════════════

class TestCleanData:
    """Tests for data cleaning and transformations."""

    def test_genre_ids_mapped_to_names(self):
        """Verifies that numeric genre_ids are mapped to text genre names."""
        df = _raw_df()
        result = clean_data(df)

        assert "genres" in result.columns
        assert "genre_ids" not in result.columns
        assert "Action" in result.loc[result["id"] == 100, "genres"].values[0]
        assert "Adventure" in result.loc[result["id"] == 100, "genres"].values[0]

    def test_unknown_genre_id_mapped(self):
        """Verifies that an unknown genre_id is mapped to 'Unknown'."""
        df = _raw_df({"genre_ids": [[99999], [28], [18]]})
        result = clean_data(df)
        assert "Unknown" in result.loc[result["id"] == 100, "genres"].values[0]

    def test_non_list_genre_ids_returns_unknown(self):
        """Verifies that non-list genre_ids return 'Unknown'."""
        df = _raw_df({"genre_ids": [None, [28], [18]]})
        result = clean_data(df)
        assert result.loc[result["id"] == 100, "genres"].values[0] == "Unknown"

    def test_release_date_converted_to_datetime(self):
        """Verifies that release_date is converted to a datetime datatype."""
        df = _raw_df()
        result = clean_data(df)
        assert pd.api.types.is_datetime64_any_dtype(result["release_date"])

    def test_invalid_release_date_becomes_nat(self):
        """Verifies that an invalid release_date is safely parsed as NaT."""
        df = _raw_df({"release_date": ["invalid-date", "2025-11-20", "2026-03-10"]})
        result = clean_data(df)
        assert pd.isna(result.loc[result["id"] == 100, "release_date"].values[0])

    def test_ingestion_timestamp_converted_to_datetime(self):
        """Verifies that ingestion_timestamp is converted to datetime and ingestion_date is created."""
        df = _raw_df()
        result = clean_data(df)
        assert pd.api.types.is_datetime64_any_dtype(result["ingestion_timestamp"])
        assert "ingestion_date" in result.columns

    def test_audience_score_calculated(self):
        """Verifies that audience_score is calculated as vote_average * 10, casted to integer."""
        df = _raw_df()
        result = clean_data(df)
        assert "audience_score" in result.columns
        # vote_average=7.8 → 78
        assert result.loc[result["id"] == 100, "audience_score"].values[0] == 78

    def test_only_expected_columns_kept(self):
        """Verifies that only expected columns are kept in the final DataFrame."""
        df = _raw_df()
        df["unexpected_column"] = "noise"
        result = clean_data(df)
        assert "unexpected_column" not in result.columns


# ═══════════════════════════════════════════
# 3. Tests for apply_data_quality()
# ═══════════════════════════════════════════

class TestApplyDataQuality:
    """Tests for data quality enforcement filters."""

    def test_filters_movies_below_vote_threshold(self):
        """Verifies that movies with vote_count below 100 are removed."""
        df = _raw_df()
        result = apply_data_quality(df)
        # id=300 has vote_count=80 → should be removed
        assert 300 not in result["id"].values
        assert len(result) == 2

    def test_removes_null_ids(self):
        """Verifies that records with null IDs are filtered out."""
        df = _raw_df({"id": [None, 200, 300], "vote_count": [500, 500, 500]})
        result = apply_data_quality(df)
        assert len(result) == 2

    def test_removes_null_titles(self):
        """Verifies that records with null titles are filtered out."""
        df = _raw_df({"title": [None, "Beta", "Gamma"], "vote_count": [500, 500, 500]})
        result = apply_data_quality(df)
        assert len(result) == 2

    def test_deduplicates_by_id(self):
        """Verifies that duplicates by ID are removed (keeping the first occurrence)."""
        df = _raw_df({
            "id": [100, 100, 200],
            "title": ["Alpha", "Alpha Copy", "Beta"],
            "vote_count": [500, 600, 400],
        })
        result = apply_data_quality(df)
        assert len(result[result["id"] == 100]) == 1

    def test_empty_df_when_all_filtered(self):
        """Verifies that an empty DataFrame is returned when no records meet the quality criteria."""
        df = _raw_df({"vote_count": [10, 20, 30]})
        result = apply_data_quality(df)
        assert result.empty

    def test_quality_preserves_all_when_threshold_met(self):
        """Verifies that all records are kept when all meet the quality threshold."""
        df = _raw_df({"vote_count": [150, 200, 300]})
        result = apply_data_quality(df)
        assert len(result) == 3


# ═══════════════════════════════════════════
# 4. Tests for invoke_gold_lambda()
# ═══════════════════════════════════════════

class TestInvokeGoldLambda:
    """Tests for invoking the downstream Gold Lambda asynchronously."""

    @patch("bronce_tmdb_to_silver.lambda_client")
    def test_invokes_with_correct_payload(self, mock_lambda):
        """Verifies that the Gold Lambda is invoked with the expected payload parameters."""
        mock_lambda.invoke.return_value = {"StatusCode": 202}
        invoke_gold_lambda("source/key.json", "s3://bucket/silver/", 50)

        mock_lambda.invoke.assert_called_once()
        call_kwargs = mock_lambda.invoke.call_args[1]
        assert call_kwargs["FunctionName"] == "silver_tmdb_to_gold"
        assert call_kwargs["InvocationType"] == "Event"

        payload = json.loads(call_kwargs["Payload"])
        assert payload["triggered_by"] == "bronce_tmdb_to_silver"
        assert payload["records_processed"] == 50

    @patch("bronce_tmdb_to_silver.lambda_client")
    def test_invocation_type_is_async(self, mock_lambda):
        """Verifies that the invocation type is asynchronous ('Event')."""
        mock_lambda.invoke.return_value = {"StatusCode": 202}
        invoke_gold_lambda("key", "path", 1)

        call_kwargs = mock_lambda.invoke.call_args[1]
        assert call_kwargs["InvocationType"] == "Event"


# ═══════════════════════════════════════════
# 5. Tests for lambda_handler
# ═══════════════════════════════════════════

class TestBronzeToSilverHandler:
    """Tests for the Bronze to Silver Lambda handler entry-point."""

    @patch("bronce_tmdb_to_silver.invoke_gold_lambda")
    @patch("bronce_tmdb_to_silver.save_silver_parquet", return_value="s3://bucket/silver/")
    @patch("bronce_tmdb_to_silver.apply_data_quality")
    @patch("bronce_tmdb_to_silver.clean_data")
    @patch("bronce_tmdb_to_silver.load_bronze_data")
    def test_handler_full_flow(self, mock_load, mock_clean, mock_quality,
                                mock_save, mock_gold):
        """Verifies the complete execution flow of the handler on valid S3 events."""
        mock_load.return_value = _raw_df()
        mock_clean.return_value = _raw_df()
        mock_quality.return_value = _raw_df({"vote_count": [500, 500, 500]})

        event = {
            "Records": [{
                "s3": {
                    "bucket": {"name": "bucket"},
                    "object": {"key": "1bronce/tmdb/popular/year=2026/data.json"},
                }
            }]
        }

        result = lambda_handler(event, None)

        assert result["statusCode"] == 200
        mock_load.assert_called_once()
        mock_clean.assert_called_once()
        mock_quality.assert_called_once()
        mock_save.assert_called_once()
        mock_gold.assert_called_once()

    def test_handler_ignores_non_bronze_prefix(self):
        """Verifies that S3 objects created outside of the bronze prefix are ignored."""
        event = {
            "Records": [{
                "s3": {
                    "bucket": {"name": "bucket"},
                    "object": {"key": "other/prefix/data.json"},
                }
            }]
        }

        result = lambda_handler(event, None)
        assert result["statusCode"] == 200
        assert "ignored" in result["body"].lower() or "ignored" in result["body"]

    @patch("bronce_tmdb_to_silver.save_silver_parquet")
    @patch("bronce_tmdb_to_silver.apply_data_quality")
    @patch("bronce_tmdb_to_silver.clean_data")
    @patch("bronce_tmdb_to_silver.load_bronze_data")
    def test_handler_returns_early_on_empty_quality(self, mock_load, mock_clean,
                                                      mock_quality, mock_save):
        """Verifies that the execution exits early without saving if no valid data remains."""
        mock_load.return_value = _raw_df()
        mock_clean.return_value = _raw_df()
        mock_quality.return_value = pd.DataFrame()  # empty

        event = {
            "Records": [{
                "s3": {
                    "bucket": {"name": "bucket"},
                    "object": {"key": "1bronce/tmdb/popular/data.json"},
                }
            }]
        }

        result = lambda_handler(event, None)
        assert result["statusCode"] == 200
        mock_save.assert_not_called()
