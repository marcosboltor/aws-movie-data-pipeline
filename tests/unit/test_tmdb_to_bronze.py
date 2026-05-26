"""
Pruebas Unitarias — Lambda tmdb_to_bronze (Ingesta TMDb → Bronze)

Valida las funciones individuales de la Lambda de ingesta:
  - Recuperación de credenciales desde Secrets Manager
  - Construcción del payload NDJSON
  - Subida a S3 con la clave de partición correcta
  - Manejo de errores de la API y de Secrets Manager
"""

import json
import pytest
import requests
from datetime import datetime
from unittest.mock import patch, MagicMock
from moto import mock_aws
import boto3

from tmdb_to_bronze import get_config, fetch_and_load, lambda_handler


# ───────────────────────────────────────────
# Helpers
# ───────────────────────────────────────────

BUCKET = "unam-2026-ingenieriadatos-equipo1-997622531618-us-east-2-an"
REGION = "us-east-2"
SECRET_NAME = "lambda-tmdb_to_bronze-s3"
SAMPLE_SECRET = {
    "TMDB_API_KEY": "fake-key",
    "TMDB_BASE_URL": "https://api.themoviedb.org/3",
    "TMDB_ENDPOINT": "/movie/popular",
    "S3_BUCKET": BUCKET,
    "S3_PREFIX": "1bronce/tmdb/popular",
}


def _build_api_page(page_num, movies):
    """Construye una respuesta paginada de TMDb."""
    return {"page": page_num, "total_pages": 5, "results": movies}


def _movie(mid, title="Movie", vote_count=500, popularity=100.0, vote_average=7.0):
    """Genera un registro mínimo de película."""
    return {
        "id": mid,
        "title": title,
        "original_title": title,
        "release_date": "2026-01-01",
        "original_language": "en",
        "genre_ids": [28],
        "popularity": popularity,
        "vote_average": vote_average,
        "vote_count": vote_count,
        "adult": False,
        "overview": f"Overview of {title}",
    }


# ═══════════════════════════════════════════
# 1. Tests para get_config()
# ═══════════════════════════════════════════

class TestGetConfig:
    """Pruebas unitarias para la recuperación de credenciales."""

    @mock_aws
    def test_get_config_returns_valid_dict(self):
        """Verifica que get_config devuelve el diccionario del secreto correctamente."""
        # Arrange
        sm = boto3.client("secretsmanager", region_name=REGION)
        sm.create_secret(
            Name=SECRET_NAME,
            SecretString=json.dumps(SAMPLE_SECRET),
        )

        with patch("tmdb_to_bronze.secrets_client", sm):
            # Act
            config = get_config()

            # Assert
            assert config["TMDB_API_KEY"] == "fake-key"
            assert config["S3_BUCKET"] == BUCKET
            assert "TMDB_BASE_URL" in config
            assert "TMDB_ENDPOINT" in config
            assert "S3_PREFIX" in config

    @mock_aws
    def test_get_config_raises_on_missing_secret(self):
        """Verifica que lanza excepción si el secreto no existe."""
        sm = boto3.client("secretsmanager", region_name=REGION)

        with patch("tmdb_to_bronze.secrets_client", sm):
            with pytest.raises(Exception, match="Error getting secret"):
                get_config()


# ═══════════════════════════════════════════
# 2. Tests para fetch_and_load()
# ═══════════════════════════════════════════

class TestFetchAndLoad:
    """Pruebas unitarias para el proceso de ingesta y carga a S3."""

    @mock_aws
    @patch("tmdb_to_bronze.requests.get")
    def test_fetch_and_load_success(self, mock_get):
        """Verifica flujo exitoso: 5 páginas → NDJSON en S3."""
        # Arrange — Secrets Manager
        sm = boto3.client("secretsmanager", region_name=REGION)
        sm.create_secret(
            Name=SECRET_NAME, SecretString=json.dumps(SAMPLE_SECRET)
        )

        # Arrange — S3
        s3 = boto3.client("s3", region_name=REGION)
        s3.create_bucket(
            Bucket=BUCKET,
            CreateBucketConfiguration={"LocationConstraint": REGION},
        )

        # Arrange — mock API responses (5 pages, 2 movies each)
        pages = []
        for p in range(1, 6):
            resp = MagicMock()
            resp.json.return_value = _build_api_page(
                p, [_movie(p * 100 + 1), _movie(p * 100 + 2)]
            )
            resp.raise_for_status = MagicMock()
            pages.append(resp)
        mock_get.side_effect = pages

        with patch("tmdb_to_bronze.secrets_client", sm), \
             patch("tmdb_to_bronze.s3", s3):
            # Act
            result = fetch_and_load()

            # Assert — response structure
            assert result["statusCode"] == 200
            body = json.loads(result["body"])
            assert body["pages_processed"] == 5
            assert body["records"] == 10  # 2 movies × 5 pages

            # Assert — object actually in S3
            objects = s3.list_objects_v2(Bucket=BUCKET, Prefix="1bronce/tmdb/popular/")
            assert objects["KeyCount"] == 1

    @mock_aws
    @patch("tmdb_to_bronze.requests.get")
    def test_fetch_and_load_writes_valid_ndjson(self, mock_get):
        """Verifica que el archivo subido a S3 es NDJSON válido."""
        sm = boto3.client("secretsmanager", region_name=REGION)
        sm.create_secret(Name=SECRET_NAME, SecretString=json.dumps(SAMPLE_SECRET))

        s3 = boto3.client("s3", region_name=REGION)
        s3.create_bucket(
            Bucket=BUCKET,
            CreateBucketConfiguration={"LocationConstraint": REGION},
        )

        resp = MagicMock()
        resp.json.return_value = _build_api_page(1, [_movie(1)])
        resp.raise_for_status = MagicMock()
        mock_get.return_value = resp

        with patch("tmdb_to_bronze.secrets_client", sm), \
             patch("tmdb_to_bronze.s3", s3):
            fetch_and_load()

        # Descargar y validar NDJSON
        objs = s3.list_objects_v2(Bucket=BUCKET, Prefix="1bronce/")
        key = objs["Contents"][0]["Key"]
        content = s3.get_object(Bucket=BUCKET, Key=key)["Body"].read().decode()
        lines = [l for l in content.strip().split("\n") if l.strip()]
        for line in lines:
            record = json.loads(line)
            assert "id" in record
            assert "title" in record
            assert "ingestion_timestamp" in record

    @mock_aws
    @patch("tmdb_to_bronze.requests.get")
    def test_s3_key_has_date_partitions(self, mock_get):
        """Verifica que la clave S3 contiene particiones year/month/day."""
        sm = boto3.client("secretsmanager", region_name=REGION)
        sm.create_secret(Name=SECRET_NAME, SecretString=json.dumps(SAMPLE_SECRET))

        s3 = boto3.client("s3", region_name=REGION)
        s3.create_bucket(
            Bucket=BUCKET,
            CreateBucketConfiguration={"LocationConstraint": REGION},
        )

        resp = MagicMock()
        resp.json.return_value = _build_api_page(1, [_movie(1)])
        resp.raise_for_status = MagicMock()
        mock_get.return_value = resp

        with patch("tmdb_to_bronze.secrets_client", sm), \
             patch("tmdb_to_bronze.s3", s3):
            fetch_and_load()

        objs = s3.list_objects_v2(Bucket=BUCKET, Prefix="1bronce/")
        key = objs["Contents"][0]["Key"]
        assert "year=" in key
        assert "month=" in key
        assert "day=" in key

    @mock_aws
    @patch("tmdb_to_bronze.requests.get")
    def test_fetch_raises_on_api_error(self, mock_get):
        """Verifica que una excepción HTTP se propaga correctamente."""
        sm = boto3.client("secretsmanager", region_name=REGION)
        sm.create_secret(Name=SECRET_NAME, SecretString=json.dumps(SAMPLE_SECRET))

        mock_get.return_value.raise_for_status.side_effect = (
            requests.exceptions.HTTPError("403 Forbidden")
        )

        with patch("tmdb_to_bronze.secrets_client", sm):
            with pytest.raises(requests.exceptions.HTTPError):
                fetch_and_load()

    @mock_aws
    @patch("tmdb_to_bronze.requests.get")
    def test_movies_cleaned_fields_only(self, mock_get):
        """Verifica que solo se conservan los campos seleccionados (sin poster_path, etc.)."""
        sm = boto3.client("secretsmanager", region_name=REGION)
        sm.create_secret(Name=SECRET_NAME, SecretString=json.dumps(SAMPLE_SECRET))

        s3 = boto3.client("s3", region_name=REGION)
        s3.create_bucket(
            Bucket=BUCKET,
            CreateBucketConfiguration={"LocationConstraint": REGION},
        )

        raw_movie = _movie(1)
        raw_movie["poster_path"] = "/fakeposter.jpg"
        raw_movie["backdrop_path"] = "/fakebackdrop.jpg"

        resp = MagicMock()
        resp.json.return_value = _build_api_page(1, [raw_movie])
        resp.raise_for_status = MagicMock()
        mock_get.return_value = resp

        with patch("tmdb_to_bronze.secrets_client", sm), \
             patch("tmdb_to_bronze.s3", s3):
            fetch_and_load()

        objs = s3.list_objects_v2(Bucket=BUCKET, Prefix="1bronce/")
        key = objs["Contents"][0]["Key"]
        content = s3.get_object(Bucket=BUCKET, Key=key)["Body"].read().decode()
        record = json.loads(content.strip().split("\n")[0])
        assert "poster_path" not in record
        assert "backdrop_path" not in record


# ═══════════════════════════════════════════
# 3. Tests para lambda_handler
# ═══════════════════════════════════════════

class TestLambdaHandler:
    """Pruebas unitarias del entry-point de la Lambda."""

    @patch("tmdb_to_bronze.fetch_and_load")
    def test_lambda_handler_delegates_to_fetch_and_load(self, mock_fetch):
        """Verifica que lambda_handler invoca fetch_and_load y retorna su resultado."""
        mock_fetch.return_value = {"statusCode": 200, "body": "ok"}
        result = lambda_handler({}, None)

        mock_fetch.assert_called_once()
        assert result["statusCode"] == 200
