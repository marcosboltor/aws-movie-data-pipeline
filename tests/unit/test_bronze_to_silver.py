"""
Pruebas Unitarias — Lambda bronze_to_silver (Bronce → Silver)

Valida las funciones de transformación y calidad de datos:
  - Carga de NDJSON desde S3
  - Limpieza de datos (mapeo de géneros, fechas, audience_score)
  - Filtros de calidad (vote_count ≥ 100, duplicados, nulos)
  - Generación de Parquet en Silver
  - Invocación de la Lambda Gold
  - Manejo del evento S3 y filtrado por prefijo
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
    """Genera un DataFrame que simula datos cargados de Bronze."""
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
# 1. Tests para load_bronze_data()
# ═══════════════════════════════════════════

class TestLoadBronzeData:
    """Pruebas de carga de datos NDJSON desde S3."""

    def test_load_parses_ndjson_correctly(self, s3_with_bronze_file):
        """Verifica que carga y parsea un NDJSON multi-línea correctamente."""
        bucket, key = s3_with_bronze_file

        with patch("bronce_tmdb_to_silver.s3") as mock_s3:
            real_s3 = boto3.client("s3", region_name="us-east-2")
            mock_s3.get_object = real_s3.get_object

            df = load_bronze_data(bucket, key)

        assert len(df) == 3
        assert "id" in df.columns
        assert "title" in df.columns

    def test_load_handles_trailing_commas(self):
        """Verifica que maneja líneas NDJSON con coma final."""
        body = '{"id": 1, "title": "A"},\n{"id": 2, "title": "B"}\n'
        mock_response = {
            "Body": MagicMock(read=MagicMock(return_value=body.encode("utf-8")))
        }

        with patch("bronce_tmdb_to_silver.s3") as mock_s3:
            mock_s3.get_object.return_value = mock_response
            df = load_bronze_data("bucket", "key")

        assert len(df) == 2

    def test_load_skips_empty_lines(self):
        """Verifica que ignora líneas vacías en el NDJSON."""
        body = '{"id": 1}\n\n\n{"id": 2}\n\n'
        mock_response = {
            "Body": MagicMock(read=MagicMock(return_value=body.encode("utf-8")))
        }

        with patch("bronce_tmdb_to_silver.s3") as mock_s3:
            mock_s3.get_object.return_value = mock_response
            df = load_bronze_data("bucket", "key")

        assert len(df) == 2


# ═══════════════════════════════════════════
# 2. Tests para clean_data()
# ═══════════════════════════════════════════

class TestCleanData:
    """Pruebas de transformación y limpieza de datos."""

    def test_genre_ids_mapped_to_names(self):
        """Verifica que los genre_ids numéricos se mapean a nombres de texto."""
        df = _raw_df()
        result = clean_data(df)

        assert "genres" in result.columns
        assert "genre_ids" not in result.columns
        assert "Action" in result.loc[result["id"] == 100, "genres"].values[0]
        assert "Adventure" in result.loc[result["id"] == 100, "genres"].values[0]

    def test_unknown_genre_id_mapped(self):
        """Verifica que un genre_id desconocido se mapea a 'Unknown'."""
        df = _raw_df({"genre_ids": [[99999], [28], [18]]})
        result = clean_data(df)
        assert "Unknown" in result.loc[result["id"] == 100, "genres"].values[0]

    def test_non_list_genre_ids_returns_unknown(self):
        """Verifica que un genre_ids no-lista genera 'Unknown'."""
        df = _raw_df({"genre_ids": [None, [28], [18]]})
        result = clean_data(df)
        assert result.loc[result["id"] == 100, "genres"].values[0] == "Unknown"

    def test_release_date_converted_to_datetime(self):
        """Verifica que release_date se convierte a datetime."""
        df = _raw_df()
        result = clean_data(df)
        assert pd.api.types.is_datetime64_any_dtype(result["release_date"])

    def test_invalid_release_date_becomes_nat(self):
        """Verifica que una fecha inválida se convierte a NaT."""
        df = _raw_df({"release_date": ["invalid-date", "2025-11-20", "2026-03-10"]})
        result = clean_data(df)
        assert pd.isna(result.loc[result["id"] == 100, "release_date"].values[0])

    def test_ingestion_timestamp_converted_to_datetime(self):
        """Verifica que ingestion_timestamp se convierte a datetime y se genera ingestion_date."""
        df = _raw_df()
        result = clean_data(df)
        assert pd.api.types.is_datetime64_any_dtype(result["ingestion_timestamp"])
        assert "ingestion_date" in result.columns

    def test_audience_score_calculated(self):
        """Verifica que audience_score = vote_average × 10, truncado a entero."""
        df = _raw_df()
        result = clean_data(df)
        assert "audience_score" in result.columns
        # vote_average=7.8 → 78
        assert result.loc[result["id"] == 100, "audience_score"].values[0] == 78

    def test_only_expected_columns_kept(self):
        """Verifica que solo se conservan las columnas esperadas."""
        df = _raw_df()
        df["unexpected_column"] = "noise"
        result = clean_data(df)
        assert "unexpected_column" not in result.columns


# ═══════════════════════════════════════════
# 3. Tests para apply_data_quality()
# ═══════════════════════════════════════════

class TestApplyDataQuality:
    """Pruebas de los filtros de calidad de datos."""

    def test_filters_movies_below_vote_threshold(self):
        """Verifica que películas con vote_count < 100 son eliminadas."""
        df = _raw_df()
        result = apply_data_quality(df)
        # id=300 has vote_count=80 → should be removed
        assert 300 not in result["id"].values
        assert len(result) == 2

    def test_removes_null_ids(self):
        """Verifica que registros con id nulo son eliminados."""
        df = _raw_df({"id": [None, 200, 300], "vote_count": [500, 500, 500]})
        result = apply_data_quality(df)
        assert len(result) == 2

    def test_removes_null_titles(self):
        """Verifica que registros con title nulo son eliminados."""
        df = _raw_df({"title": [None, "Beta", "Gamma"], "vote_count": [500, 500, 500]})
        result = apply_data_quality(df)
        assert len(result) == 2

    def test_deduplicates_by_id(self):
        """Verifica que duplicados por id se eliminan (conserva primer registro)."""
        df = _raw_df({
            "id": [100, 100, 200],
            "title": ["Alpha", "Alpha Copy", "Beta"],
            "vote_count": [500, 600, 400],
        })
        result = apply_data_quality(df)
        assert len(result[result["id"] == 100]) == 1

    def test_empty_df_when_all_filtered(self):
        """Verifica que un DataFrame vacío se retorna cuando ninguno pasa los filtros."""
        df = _raw_df({"vote_count": [10, 20, 30]})
        result = apply_data_quality(df)
        assert result.empty

    def test_quality_preserves_all_when_threshold_met(self):
        """Verifica que todos los registros se conservan si cumplen los criterios."""
        df = _raw_df({"vote_count": [150, 200, 300]})
        result = apply_data_quality(df)
        assert len(result) == 3


# ═══════════════════════════════════════════
# 4. Tests para invoke_gold_lambda()
# ═══════════════════════════════════════════

class TestInvokeGoldLambda:
    """Pruebas de la invocación asíncrona de la Lambda Gold."""

    @patch("bronce_tmdb_to_silver.lambda_client")
    def test_invokes_with_correct_payload(self, mock_lambda):
        """Verifica que se invoca la Lambda Gold con el payload correcto."""
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
        """Verifica que la invocación es asíncrona (Event, no RequestResponse)."""
        mock_lambda.invoke.return_value = {"StatusCode": 202}
        invoke_gold_lambda("key", "path", 1)

        call_kwargs = mock_lambda.invoke.call_args[1]
        assert call_kwargs["InvocationType"] == "Event"


# ═══════════════════════════════════════════
# 5. Tests para lambda_handler
# ═══════════════════════════════════════════

class TestBronzeToSilverHandler:
    """Pruebas del entry-point de la Lambda Bronze→Silver."""

    @patch("bronce_tmdb_to_silver.invoke_gold_lambda")
    @patch("bronce_tmdb_to_silver.save_silver_parquet", return_value="s3://bucket/silver/")
    @patch("bronce_tmdb_to_silver.apply_data_quality")
    @patch("bronce_tmdb_to_silver.clean_data")
    @patch("bronce_tmdb_to_silver.load_bronze_data")
    def test_handler_full_flow(self, mock_load, mock_clean, mock_quality,
                                mock_save, mock_gold):
        """Verifica el flujo completo del handler con datos válidos."""
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
        """Verifica que archivos fuera de 1bronce/tmdb/popular/ son ignorados."""
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
        assert "ignorado" in result["body"].lower() or "ignorado" in result["body"]

    @patch("bronce_tmdb_to_silver.save_silver_parquet")
    @patch("bronce_tmdb_to_silver.apply_data_quality")
    @patch("bronce_tmdb_to_silver.clean_data")
    @patch("bronce_tmdb_to_silver.load_bronze_data")
    def test_handler_returns_early_on_empty_quality(self, mock_load, mock_clean,
                                                      mock_quality, mock_save):
        """Verifica que retorna sin guardar si no hay datos válidos."""
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
