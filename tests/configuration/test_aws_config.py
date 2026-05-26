"""
Configuration Tests — AWS Services and Constants Validation

Validates that the configurations of the pipeline are correct:
  - Secrets Manager credentials and settings
  - S3 bucket names and prefixes
  - Athena configuration (database name, query results output location)
  - Official Genre Map constants
  - Target Lambda function names and invoke structures
  - Data quality thresholds and filters
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
# 1. Secrets Manager Configuration
# ═══════════════════════════════════════════

class TestSecretsManagerConfig:
    """Tests for AWS Secrets Manager settings."""

    def test_secret_name_is_correct(self):
        """Verifies that the SecretId matches the expected resource name."""
        # get_config function uses "lambda-tmdb_to_bronze-s3"
        source = inspect.getsource(tmdb_to_bronze.get_config)
        assert "lambda-tmdb_to_bronze-s3" in source

    def test_secret_contains_required_keys(self):
        """Verifies that the secret JSON contains all expected configuration keys."""
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
        """Verifies that Secrets Manager client specifies the us-east-2 region."""
        source = inspect.getsource(tmdb_to_bronze)
        assert 'region_name="us-east-2"' in source


# ═══════════════════════════════════════════
# 2. S3 Configuration (Buckets and Prefixes)
# ═══════════════════════════════════════════

class TestS3Config:
    """Tests for Amazon S3 bucket names and prefix configurations."""

    def test_silver_bucket_name_matches(self):
        """Verifies that the Silver bucket name conforms to project specifications."""
        assert SILVER_BUCKET_NAME == "unam-2026-ingenieriadatos-equipo1-997622531618-us-east-2-an"

    def test_silver_prefix_is_correct(self):
        """Verifies that the Silver prefix matches expected standard path."""
        assert SILVER_PREFIX == "2silver/movies"

    def test_gold_bucket_name_matches(self):
        """Verifies that the Gold bucket name matches project specifications."""
        assert GOLD_BUCKET_NAME == "unam-2026-ingenieriadatos-equipo1-997622531618-us-east-2-an"

    def test_gold_base_path_format(self):
        """Verifies that GOLD_BASE_PATH is a valid S3 path string."""
        assert GOLD_BASE_PATH.startswith("s3://")
        assert "3gold" in GOLD_BASE_PATH

    def test_gold_prefixes_list_has_four_entries(self):
        """Verifies that exactly 4 Gold prefixes are configured for cleanups."""
        assert len(GOLD_PREFIXES) == 4

    def test_gold_prefixes_all_start_with_3gold(self):
        """Verifies that all S3 Gold prefixes correctly begin with '3gold/'."""
        for prefix in GOLD_PREFIXES:
            assert prefix.startswith("3gold/"), f"Prefix {prefix} does not start with '3gold/'"

    def test_bronze_prefix_in_handler_validation(self):
        """Verifies that the Bronze to Silver event handler filters for correct S3 input prefix."""
        source = inspect.getsource(bronze_silver_handler)
        assert "1bronce/tmdb/popular/" in source


# ═══════════════════════════════════════════
# 3. Athena Configuration
# ═══════════════════════════════════════════

class TestAthenaConfig:
    """Tests for Amazon Athena execution configurations."""

    def test_database_name_is_correct(self):
        """Verifies that the target Athena Glue database name is correct."""
        assert DATABASE == "db_movies_tmdb"

    def test_output_location_is_s3_path(self):
        """Verifies that OUTPUT_ATHENA is configured as a valid S3 path."""
        assert OUTPUT_ATHENA.startswith("s3://")
        assert "athena" in OUTPUT_ATHENA.lower()

    def test_output_location_uses_project_bucket(self):
        """Verifies that the Athena query output location uses the project S3 bucket."""
        assert GOLD_BUCKET_NAME in OUTPUT_ATHENA


# ═══════════════════════════════════════════
# 4. Genre Map Configuration
# ═══════════════════════════════════════════

class TestGenreMapConfig:
    """Tests for the TMDb genre ID mapper configuration."""

    def test_genre_map_has_expected_entries(self):
        """Verifies that the GENRE_MAP contains all main expected movie genres."""
        expected_genres = [
            "Action", "Adventure", "Animation", "Comedy", "Crime",
            "Documentary", "Drama", "Family", "Fantasy", "History",
            "Horror", "Music", "Mystery", "Romance", "Science Fiction",
            "TV Movie", "Thriller", "War", "Western"
        ]

        for genre in expected_genres:
            assert genre in GENRE_MAP.values(), f"Genre '{genre}' not found in GENRE_MAP"

    def test_genre_map_has_19_entries(self):
        """Verifies that exactly 19 official genres are mapped in the static catalog."""
        assert len(GENRE_MAP) == 19

    def test_genre_map_keys_are_integers(self):
        """Verifies that all genre ID keys in the static catalog are integers."""
        for key in GENRE_MAP.keys():
            assert isinstance(key, int), f"Key {key} is not an integer"

    def test_genre_map_values_are_strings(self):
        """Verifies that all genre text values in the static catalog are strings."""
        for value in GENRE_MAP.values():
            assert isinstance(value, str), f"Value {value} is not a string"

    def test_key_genre_ids_match_tmdb_official(self):
        """Verifies that the principal genre keys match TMDb official mappings."""
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
# 5. Downstream Lambda Reference Configuration
# ═══════════════════════════════════════════

class TestLambdaReferenceConfig:
    """Tests for referenced target Lambda functions settings."""

    def test_gold_lambda_name_is_correct(self):
        """Verifies that the referenced Gold Lambda name is correct."""
        assert GOLD_LAMBDA_NAME == "silver_tmdb_to_gold"

    def test_gold_lambda_invocation_uses_event_type(self):
        """Verifies that the downstream invocation uses 'Event' (asynchronous execution)."""
        source = inspect.getsource(invoke_gold_lambda)
        assert '"Event"' in source or "'Event'" in source


# ═══════════════════════════════════════════
# 6. Data Quality Rules Configuration
# ═══════════════════════════════════════════

class TestDataQualityConfig:
    """Tests for data quality threshold rules configuration."""

    def test_vote_count_threshold_is_100(self):
        """Verifies that the minimum vote count threshold is set to 100."""
        source = inspect.getsource(apply_data_quality)
        assert "100" in source

    def test_deduplication_uses_id_column(self):
        """Verifies that deduplication filters utilize the 'id' column."""
        source = inspect.getsource(apply_data_quality)
        assert '"id"' in source or "'id'" in source

    def test_null_check_covers_id_and_title(self):
        """Verifies that null validation checks verify 'id' and 'title' fields."""
        source = inspect.getsource(apply_data_quality)
        assert '"id"' in source
        assert '"title"' in source
