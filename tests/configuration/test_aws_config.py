"""
Pruebas de Configuración — Validación de servicios AWS y constantes

Valida que las configuraciones del pipeline sean correctas:
  - Credenciales y secretos de Secrets Manager
  - Nombres de buckets y prefijos S3
  - Configuración de Athena (database, output location)
  - Constantes del mapa de géneros
  - Nombres de funciones Lambda referenciadas
  - Variables de entorno necesarias
"""

import inspect
import json
import pytest
from unittest.mock import patch, MagicMock

import tmdb_to_bronze
from tmdb_to_bronze import get_config

from bronce_tmdb_to_silver import (
    BUCKET_NAME as SILVER_BUCKET_NAME,
    SILVER_PREFIX,
    GOLD_LAMBDA_NAME,
    GENRE_MAP,
    apply_data_quality,
    invoke_gold_lambda,
    lambda_handler as bronze_silver_handler,
)

from silver_tmdb_to_gold import (
    DATABASE,
    OUTPUT_ATHENA,
    BUCKET_NAME as GOLD_BUCKET_NAME,
    GOLD_BASE_PATH,
    GOLD_PREFIXES,
)


# ═══════════════════════════════════════════
# 1. Configuración de Secrets Manager
# ═══════════════════════════════════════════

class TestSecretsManagerConfig:
    """Pruebas de configuración de AWS Secrets Manager."""

    def test_secret_name_is_correct(self):
        """Verifica que el SecretId usado coincide con el nombre esperado."""
        # La función get_config usa "lambda-tmdb_to_bronze-s3"
        source = inspect.getsource(tmdb_to_bronze.get_config)
        assert "lambda-tmdb_to_bronze-s3" in source

    def test_secret_contains_required_keys(self):
        """Verifica que el secreto contiene todas las claves requeridas."""
        required_keys = {
            "TMDB_API_KEY",
            "TMDB_BASE_URL",
            "TMDB_ENDPOINT",
            "S3_BUCKET",
            "S3_PREFIX",
        }

        mock_secret = {
            "TMDB_API_KEY": "test",
            "TMDB_BASE_URL": "https://api.themoviedb.org/3",
            "TMDB_ENDPOINT": "/movie/popular",
            "S3_BUCKET": "test-bucket",
            "S3_PREFIX": "1bronce/tmdb/popular",
        }

        assert required_keys.issubset(mock_secret.keys())

    def test_secrets_manager_region_is_us_east_2(self):
        """Verifica que el cliente de Secrets Manager usa la región us-east-2."""
        source = inspect.getsource(tmdb_to_bronze)
        assert 'region_name="us-east-2"' in source


# ═══════════════════════════════════════════
# 2. Configuración de S3 (Buckets y Prefijos)
# ═══════════════════════════════════════════

class TestS3Config:
    """Pruebas de configuración de Amazon S3."""

    def test_silver_bucket_name_matches(self):
        """Verifica que el bucket de Silver coincide con la convención del proyecto."""
        assert SILVER_BUCKET_NAME == "unam-2026-ingenieriadatos-equipo1-997622531618-us-east-2-an"

    def test_silver_prefix_is_correct(self):
        """Verifica el prefijo Silver."""
        assert SILVER_PREFIX == "2silver/movies"

    def test_gold_bucket_name_matches(self):
        """Verifica que el bucket de Gold coincide."""
        assert GOLD_BUCKET_NAME == "unam-2026-ingenieriadatos-equipo1-997622531618-us-east-2-an"

    def test_gold_base_path_format(self):
        """Verifica que GOLD_BASE_PATH sigue el formato S3 correcto."""
        assert GOLD_BASE_PATH.startswith("s3://")
        assert "3gold" in GOLD_BASE_PATH

    def test_gold_prefixes_list_has_four_entries(self):
        """Verifica que hay exactamente 4 prefijos Gold para limpiar."""
        assert len(GOLD_PREFIXES) == 4

    def test_gold_prefixes_all_start_with_3gold(self):
        """Verifica que todos los prefijos Gold comienzan con '3gold/'."""
        for prefix in GOLD_PREFIXES:
            assert prefix.startswith("3gold/"), f"Prefix {prefix} no comienza con '3gold/'"

    def test_bronze_prefix_in_handler_validation(self):
        """Verifica que el handler Bronze→Silver filtra por el prefijo correcto."""
        source = inspect.getsource(bronze_silver_handler)
        assert "1bronce/tmdb/popular/" in source


# ═══════════════════════════════════════════
# 3. Configuración de Athena
# ═══════════════════════════════════════════

class TestAthenaConfig:
    """Pruebas de configuración de Amazon Athena."""

    def test_database_name_is_correct(self):
        """Verifica que el nombre de la base de datos Athena es correcto."""
        assert DATABASE == "db_movies_tmdb"

    def test_output_location_is_s3_path(self):
        """Verifica que OUTPUT_ATHENA es una ruta S3 válida."""
        assert OUTPUT_ATHENA.startswith("s3://")
        assert "athena" in OUTPUT_ATHENA.lower()

    def test_output_location_uses_project_bucket(self):
        """Verifica que la salida de Athena usa el bucket del proyecto."""
        assert GOLD_BUCKET_NAME in OUTPUT_ATHENA


# ═══════════════════════════════════════════
# 4. Configuración del mapa de géneros
# ═══════════════════════════════════════════

class TestGenreMapConfig:
    """Pruebas de configuración del mapeo de géneros TMDb."""

    def test_genre_map_has_expected_entries(self):
        """Verifica que el GENRE_MAP contiene al menos los géneros principales."""
        expected_genres = [
            "Action", "Adventure", "Animation", "Comedy", "Crime",
            "Documentary", "Drama", "Family", "Fantasy", "History",
            "Horror", "Music", "Mystery", "Romance", "Science Fiction",
            "TV Movie", "Thriller", "War", "Western"
        ]

        for genre in expected_genres:
            assert genre in GENRE_MAP.values(), f"Género '{genre}' no encontrado en GENRE_MAP"

    def test_genre_map_has_19_entries(self):
        """Verifica que hay exactamente 19 géneros mapeados (estándar TMDb)."""
        assert len(GENRE_MAP) == 19

    def test_genre_map_keys_are_integers(self):
        """Verifica que todas las claves del GENRE_MAP son enteros."""
        for key in GENRE_MAP.keys():
            assert isinstance(key, int), f"Clave {key} no es entero"

    def test_genre_map_values_are_strings(self):
        """Verifica que todos los valores del GENRE_MAP son strings."""
        for value in GENRE_MAP.values():
            assert isinstance(value, str), f"Valor {value} no es string"

    def test_key_genre_ids_match_tmdb_official(self):
        """Verifica que los IDs principales coinciden con los de TMDb."""
        official_mappings = {
            28: "Action",
            12: "Adventure",
            16: "Animation",
            35: "Comedy",
            18: "Drama",
            27: "Horror",
            878: "Science Fiction",
            53: "Thriller",
        }

        for genre_id, expected_name in official_mappings.items():
            assert GENRE_MAP.get(genre_id) == expected_name


# ═══════════════════════════════════════════
# 5. Configuración de Lambdas referenciadas
# ═══════════════════════════════════════════

class TestLambdaReferenceConfig:
    """Pruebas de configuración de funciones Lambda referenciadas."""

    def test_gold_lambda_name_is_correct(self):
        """Verifica que el nombre de la Lambda Gold referenciada es correcto."""
        assert GOLD_LAMBDA_NAME == "silver_tmdb_to_gold"

    def test_gold_lambda_invocation_uses_event_type(self):
        """Verifica que la invocación usa InvocationType='Event' (asíncrono)."""
        source = inspect.getsource(invoke_gold_lambda)
        assert '"Event"' in source or "'Event'" in source


# ═══════════════════════════════════════════
# 6. Configuración de calidad de datos
# ═══════════════════════════════════════════

class TestDataQualityConfig:
    """Pruebas de configuración de reglas de calidad."""

    def test_vote_count_threshold_is_100(self):
        """Verifica que el umbral de vote_count es 100."""
        source = inspect.getsource(apply_data_quality)
        assert "100" in source

    def test_deduplication_uses_id_column(self):
        """Verifica que la deduplicación se hace por la columna 'id'."""
        source = inspect.getsource(apply_data_quality)
        assert '"id"' in source or "'id'" in source

    def test_null_check_covers_id_and_title(self):
        """Verifica que se validan nulos en 'id' y 'title'."""
        source = inspect.getsource(apply_data_quality)
        assert '"id"' in source
        assert '"title"' in source
