"""
Pruebas de Integración — Flujo Bronze → Silver

Valida que las funciones de carga, limpieza y calidad trabajan
juntas correctamente como una cadena integrada, simulando un flujo
de extremo a extremo dentro de la capa Bronze→Silver.
"""

import json
import pytest
import pandas as pd
from datetime import datetime
from unittest.mock import patch, MagicMock

from bronce_tmdb_to_silver import (
    load_bronze_data,
    clean_data,
    apply_data_quality,
    lambda_handler as bronze_to_silver_handler,
)
from silver_tmdb_to_gold import lambda_handler as silver_to_gold_handler


# ───────────────────────────────────────────
# Helpers
# ───────────────────────────────────────────

def _ndjson_body(movies):
    """Genera un cuerpo NDJSON desde una lista de dicts."""
    return "\n".join(json.dumps(m, ensure_ascii=False) for m in movies)


def _movie(mid, title, vote_count=500, genres=None, popularity=100.0, vote_avg=7.0):
    """Genera un registro de película para tests de integración."""
    return {
        "id": mid,
        "title": title,
        "original_title": title,
        "release_date": "2026-01-15",
        "original_language": "en",
        "genre_ids": genres or [28],
        "popularity": popularity,
        "vote_average": vote_avg,
        "vote_count": vote_count,
        "adult": False,
        "overview": f"Overview for {title}",
        "source_page": 1,
        "ingestion_timestamp": datetime(2026, 5, 1, 12, 0, 0).isoformat(),
    }


# ═══════════════════════════════════════════
# 1. Integración: load → clean → quality
# ═══════════════════════════════════════════

class TestBronzeToSilverIntegration:
    """Pruebas de integración para la cadena completa load→clean→quality."""

    def test_full_pipeline_load_clean_quality(self):
        """
        Integración: carga NDJSON → limpieza de datos → filtros de calidad.
        Verifica que solo pasan películas con vote_count ≥ 100.
        """
        movies = [
            _movie(1, "High Votes", vote_count=500, genres=[28, 12]),
            _movie(2, "Low Votes", vote_count=50, genres=[18]),
            _movie(3, "Medium Votes", vote_count=150, genres=[35, 80]),
        ]
        body = _ndjson_body(movies)

        mock_response = {
            "Body": MagicMock(read=MagicMock(return_value=body.encode("utf-8")))
        }

        with patch("bronce_tmdb_to_silver.s3") as mock_s3:
            mock_s3.get_object.return_value = mock_response
            df_raw = load_bronze_data("bucket", "key")

        df_clean = clean_data(df_raw)
        df_quality = apply_data_quality(df_clean)

        # Solo 2 películas pasan el filtro de vote_count ≥ 100
        assert len(df_quality) == 2
        assert set(df_quality["id"].values) == {1, 3}

        # Verificar que los géneros fueron mapeados
        assert "genres" in df_quality.columns
        assert "Action" in df_quality.loc[df_quality["id"] == 1, "genres"].values[0]

    def test_genres_properly_mapped_through_pipeline(self):
        """Integración: verifica mapeo de géneros múltiples a lo largo del pipeline."""
        movies = [
            _movie(1, "Multi Genre", vote_count=200, genres=[28, 12, 878]),
        ]
        body = _ndjson_body(movies)

        mock_response = {
            "Body": MagicMock(read=MagicMock(return_value=body.encode("utf-8")))
        }

        with patch("bronce_tmdb_to_silver.s3") as mock_s3:
            mock_s3.get_object.return_value = mock_response
            df_raw = load_bronze_data("bucket", "key")

        df_clean = clean_data(df_raw)
        df_final = apply_data_quality(df_clean)

        genres = df_final.loc[df_final["id"] == 1, "genres"].values[0]
        assert "Action" in genres
        assert "Adventure" in genres
        assert "Science Fiction" in genres

    def test_deduplication_through_pipeline(self):
        """Integración: registros duplicados son eliminados tras calidad."""
        movies = [
            _movie(1, "Movie A", vote_count=300),
            _movie(1, "Movie A Duplicate", vote_count=400),
            _movie(2, "Movie B", vote_count=200),
        ]
        body = _ndjson_body(movies)

        mock_response = {
            "Body": MagicMock(read=MagicMock(return_value=body.encode("utf-8")))
        }

        with patch("bronce_tmdb_to_silver.s3") as mock_s3:
            mock_s3.get_object.return_value = mock_response
            df_raw = load_bronze_data("bucket", "key")

        df_clean = clean_data(df_raw)
        df_quality = apply_data_quality(df_clean)

        assert len(df_quality) == 2
        assert len(df_quality[df_quality["id"] == 1]) == 1

    def test_audience_score_survives_pipeline(self):
        """Integración: audience_score se calcula y sobrevive todos los pasos."""
        movies = [_movie(1, "Scored Movie", vote_count=200, vote_avg=8.5)]
        body = _ndjson_body(movies)

        mock_response = {
            "Body": MagicMock(read=MagicMock(return_value=body.encode("utf-8")))
        }

        with patch("bronce_tmdb_to_silver.s3") as mock_s3:
            mock_s3.get_object.return_value = mock_response
            df_raw = load_bronze_data("bucket", "key")

        df_clean = clean_data(df_raw)
        df_final = apply_data_quality(df_clean)

        assert "audience_score" in df_final.columns
        assert df_final["audience_score"].values[0] == 85  # 8.5 × 10


# ═══════════════════════════════════════════
# 2. Integración: handler con flujo real
# ═══════════════════════════════════════════

class TestBronzeToSilverHandlerIntegration:
    """Pruebas de integración del handler completo con mocks de I/O."""

    @patch("bronce_tmdb_to_silver.invoke_gold_lambda")
    @patch("bronce_tmdb_to_silver.save_silver_parquet", return_value="s3://bucket/silver/")
    def test_handler_processes_valid_s3_event(self, mock_save, mock_gold):
        """
        Integración: simula un S3 event real y verifica que el handler
        ejecuta el pipeline completo hasta invocar la Lambda Gold.
        """
        movies = [
            _movie(1, "Valid Movie", vote_count=500),
            _movie(2, "Also Valid", vote_count=300),
        ]
        body = _ndjson_body(movies)

        mock_response = {
            "Body": MagicMock(read=MagicMock(return_value=body.encode("utf-8")))
        }

        event = {
            "Records": [{
                "s3": {
                    "bucket": {"name": "my-bucket"},
                    "object": {"key": "1bronce/tmdb/popular/data.json"},
                }
            }]
        }

        with patch("bronce_tmdb_to_silver.s3") as mock_s3:
            mock_s3.get_object.return_value = mock_response
            result = bronze_to_silver_handler(event, None)

        assert result["statusCode"] == 200
        body_parsed = json.loads(result["body"])
        assert body_parsed["records_processed"] == 2
        mock_save.assert_called_once()
        mock_gold.assert_called_once()

    @patch("bronce_tmdb_to_silver.invoke_gold_lambda")
    @patch("bronce_tmdb_to_silver.save_silver_parquet")
    def test_handler_skips_gold_when_no_valid_data(self, mock_save, mock_gold):
        """
        Integración: todos los registros tienen vote_count bajo →
        no se guarda Parquet ni se invoca Gold.
        """
        movies = [
            _movie(1, "Low Votes 1", vote_count=10),
            _movie(2, "Low Votes 2", vote_count=20),
        ]
        body = _ndjson_body(movies)

        mock_response = {
            "Body": MagicMock(read=MagicMock(return_value=body.encode("utf-8")))
        }

        event = {
            "Records": [{
                "s3": {
                    "bucket": {"name": "my-bucket"},
                    "object": {"key": "1bronce/tmdb/popular/data.json"},
                }
            }]
        }

        with patch("bronce_tmdb_to_silver.s3") as mock_s3:
            mock_s3.get_object.return_value = mock_response
            result = bronze_to_silver_handler(event, None)

        assert result["statusCode"] == 200
        mock_save.assert_not_called()
        mock_gold.assert_not_called()


# ═══════════════════════════════════════════
# 3. Integración: Silver → Gold secuencial
# ═══════════════════════════════════════════

class TestSilverToGoldIntegration:
    """Pruebas de integración para el flujo completo Silver→Gold."""

    @patch("silver_tmdb_to_gold.clean_s3_prefix")
    @patch("silver_tmdb_to_gold.run_query")
    def test_full_gold_pipeline_sequence(self, mock_run, mock_clean):
        """
        Integración: verifica que la secuencia DROP → clean → CTAS se 
        ejecuta en el orden correcto.
        """
        call_order = []
        mock_run.side_effect = lambda q: call_order.append(("query", q[:30]))
        mock_clean.side_effect = lambda b, p: call_order.append(("clean", p))

        event = {
            "triggered_by": "bronce_tmdb_to_silver",
            "source_file": "test.json",
            "silver_output_path": "s3://bucket/silver/",
            "records_processed": 10,
        }

        result = silver_to_gold_handler(event, None)
        assert result["statusCode"] == 200

        # First 5 operations should be DROP queries
        for i in range(5):
            assert call_order[i][0] == "query"
            assert "DROP" in call_order[i][1].upper()

        # Then S3 clean operations
        clean_ops = [op for op in call_order if op[0] == "clean"]
        assert len(clean_ops) == 4

    @patch("silver_tmdb_to_gold.clean_s3_prefix")
    @patch("silver_tmdb_to_gold.run_query")
    def test_gold_tables_reference_silver_source(self, mock_run, mock_clean):
        """
        Integración: verifica que las CTAS leen desde la tabla Silver ('2silver').
        """
        silver_to_gold_handler({}, None)

        ctas_queries = [
            c[0][0] for c in mock_run.call_args_list
            if "CREATE TABLE" in c[0][0]
        ]
        for query in ctas_queries:
            assert '"2silver"' in query or "2silver" in query
