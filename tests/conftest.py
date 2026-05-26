"""
Shared pytest fixtures for the AWS TMDb Medallion Pipeline test suite.

Provides reusable mocked AWS services (S3, Secrets Manager, Lambda, Athena),
sample TMDb API responses, and preconfigured DataFrames for all test layers.
"""

import json
import os
import sys
import pytest
import boto3
from datetime import datetime
from unittest.mock import MagicMock, patch
from moto import mock_aws

# ---------------------------------------------------------------------------
# Set dummy AWS env vars BEFORE importing Lambda modules (they create
# boto3 clients at module level which requires a region)
# ---------------------------------------------------------------------------
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-2")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")

# ---------------------------------------------------------------------------
# Ensure src/lambda subdirectories are importable
# ---------------------------------------------------------------------------
LAMBDA_BASE = os.path.join(
    os.path.dirname(__file__), os.pardir, "src", "lambda"
)
for sub in ("bronze_to_silver", "tmdb_to_bronze", "silver_to_gold"):
    path = os.path.abspath(os.path.join(LAMBDA_BASE, sub))
    if path not in sys.path:
        sys.path.insert(0, path)


# ===========================
# Constants
# ===========================

TEST_BUCKET = "unam-2026-ingenieriadatos-equipo1-997622531618-us-east-2-an"
TEST_REGION = "us-east-2"
TEST_SECRET_NAME = "lambda-tmdb_to_bronze-s3"

SAMPLE_SECRET = {
    "TMDB_API_KEY": "fake-api-key-for-tests",
    "TMDB_BASE_URL": "https://api.themoviedb.org/3",
    "TMDB_ENDPOINT": "/movie/popular",
    "S3_BUCKET": TEST_BUCKET,
    "S3_PREFIX": "1bronce/tmdb/popular",
}


# ===========================
# Sample TMDb API response
# ===========================

@pytest.fixture
def sample_tmdb_page():
    """Returns a single page of TMDb popular-movies API response."""
    return {
        "page": 1,
        "total_pages": 500,
        "total_results": 10000,
        "results": [
            {
                "id": 100,
                "title": "Test Movie Alpha",
                "original_title": "Test Movie Alpha",
                "release_date": "2026-01-15",
                "original_language": "en",
                "genre_ids": [28, 12],
                "popularity": 150.5,
                "vote_average": 7.8,
                "vote_count": 1200,
                "adult": False,
                "overview": "An action-packed adventure.",
            },
            {
                "id": 200,
                "title": "Test Movie Beta",
                "original_title": "Test Movie Beta",
                "release_date": "2025-11-20",
                "original_language": "es",
                "genre_ids": [18, 35],
                "popularity": 45.2,
                "vote_average": 6.1,
                "vote_count": 350,
                "adult": False,
                "overview": "A dramatic comedy.",
            },
            {
                "id": 300,
                "title": "Test Movie Gamma",
                "original_title": "Test Movie Gamma",
                "release_date": "2026-03-10",
                "original_language": "en",
                "genre_ids": [27, 53],
                "popularity": 200.0,
                "vote_average": 5.5,
                "vote_count": 80,
                "adult": False,
                "overview": "A terrifying thriller.",
            },
        ],
    }


@pytest.fixture
def sample_ndjson_body():
    """Returns NDJSON content simulating a Bronze file in S3."""
    ts = datetime(2026, 5, 1, 12, 0, 0).isoformat()
    records = [
        {
            "id": 100,
            "title": "Test Movie Alpha",
            "original_title": "Test Movie Alpha",
            "release_date": "2026-01-15",
            "original_language": "en",
            "genre_ids": [28, 12],
            "popularity": 150.5,
            "vote_average": 7.8,
            "vote_count": 1200,
            "adult": False,
            "overview": "An action-packed adventure.",
            "source_page": 1,
            "ingestion_timestamp": ts,
        },
        {
            "id": 200,
            "title": "Test Movie Beta",
            "original_title": "Test Movie Beta",
            "release_date": "2025-11-20",
            "original_language": "es",
            "genre_ids": [18, 35],
            "popularity": 45.2,
            "vote_average": 6.1,
            "vote_count": 350,
            "adult": False,
            "overview": "A dramatic comedy.",
            "source_page": 1,
            "ingestion_timestamp": ts,
        },
        {
            "id": 300,
            "title": "Test Movie Gamma",
            "original_title": "Test Movie Gamma",
            "release_date": "2026-03-10",
            "original_language": "en",
            "genre_ids": [27, 53],
            "popularity": 200.0,
            "vote_average": 5.5,
            "vote_count": 80,  # Below quality threshold
            "adult": False,
            "overview": "A terrifying thriller.",
            "source_page": 1,
            "ingestion_timestamp": ts,
        },
    ]
    return "\n".join(json.dumps(r, ensure_ascii=False) for r in records)


# ===========================
# Mocked AWS environment
# ===========================

@pytest.fixture
def aws_credentials():
    """Set dummy AWS credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = TEST_REGION
    yield
    for key in (
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_SECURITY_TOKEN",
        "AWS_SESSION_TOKEN",
        "AWS_DEFAULT_REGION",
    ):
        os.environ.pop(key, None)


@pytest.fixture
def s3_bucket(aws_credentials):
    """Creates a mocked S3 bucket using moto."""
    with mock_aws():
        s3 = boto3.client("s3", region_name=TEST_REGION)
        s3.create_bucket(
            Bucket=TEST_BUCKET,
            CreateBucketConfiguration={"LocationConstraint": TEST_REGION},
        )
        yield s3


@pytest.fixture
def secrets_manager(aws_credentials):
    """Creates a mocked Secrets Manager with the TMDb secret."""
    with mock_aws():
        client = boto3.client("secretsmanager", region_name=TEST_REGION)
        client.create_secret(
            Name=TEST_SECRET_NAME,
            SecretString=json.dumps(SAMPLE_SECRET),
        )
        yield client


@pytest.fixture
def s3_with_bronze_file(s3_bucket, sample_ndjson_body):
    """
    Creates the S3 bucket and uploads a sample Bronze NDJSON file.
    Returns the (bucket_name, key) tuple.
    """
    key = "1bronce/tmdb/popular/year=2026/month=05/day=01/data_2026-05-01T12-00-00.json"
    s3_bucket.put_object(
        Bucket=TEST_BUCKET,
        Key=key,
        Body=sample_ndjson_body.encode("utf-8"),
        ContentType="application/json",
    )
    return TEST_BUCKET, key


@pytest.fixture
def s3_event_notification():
    """Returns a sample S3 event notification as received by the Bronze-to-Silver Lambda."""
    return {
        "Records": [
            {
                "s3": {
                    "bucket": {"name": TEST_BUCKET},
                    "object": {
                        "key": "1bronce/tmdb/popular/year=2026/month=05/day=01/data_2026-05-01T12-00-00.json"
                    },
                }
            }
        ]
    }


@pytest.fixture
def gold_event():
    """Returns a sample event payload for the Silver-to-Gold Lambda."""
    return {
        "triggered_by": "bronce_tmdb_to_silver",
        "source_file": "1bronce/tmdb/popular/year=2026/month=05/day=01/data_2026-05-01T12-00-00.json",
        "silver_output_path": f"s3://{TEST_BUCKET}/2silver/movies/year=2026/month=05/day=01/",
        "records_processed": 2,
    }
