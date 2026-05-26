import requests
import json
import boto3
from datetime import datetime, timezone

s3 = boto3.client("s3")
secrets_client = boto3.client("secretsmanager", region_name="us-east-2")


def get_config():
    """
    Retrieves configuration and credentials from AWS Secrets Manager.
    
    Returns:
        dict: A dictionary containing the configuration variables 
              (e.g., TMDB API keys, S3 bucket settings).
    
    Raises:
        Exception: If there is an error retrieving or parsing the secret.
    """
    try:
        response = secrets_client.get_secret_value(
            SecretId="lambda-tmdb_to_bronze-s3"
        )
        return json.loads(response["SecretString"])
    except Exception as e:
        raise Exception(f"Error getting secret: {str(e)}")


def fetch_and_load():
    """
    Fetches the first 5 pages of popular movies from the TMDb API, cleans the data, 
    and loads it into an AWS S3 bucket as an NDJSON file (Bronze layer).
    
    Returns:
        dict: An HTTP-like response dictionary containing the status code and a JSON body 
              with ingestion metrics (pages processed, records ingested, S3 path, and timestamp).
    """
    config = get_config()

    API_KEY = config["TMDB_API_KEY"]
    BASE_URL = config["TMDB_BASE_URL"]
    ENDPOINT = config["TMDB_ENDPOINT"]
    BUCKET = config["S3_BUCKET"]
    PREFIX = config["S3_PREFIX"]

    url = f"{BASE_URL}{ENDPOINT}"

    now = datetime.now(timezone.utc)
    ingestion_timestamp = now.isoformat()

    movies_clean = []

    # Traemos las primeras 5 páginas de TMDb
    for page in range(1, 6):
        params = {
            "api_key": API_KEY,
            "language": "en-US",
            "page": page
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        for movie in data.get("results", []):
            movies_clean.append({
                "id": movie.get("id"),
                "title": movie.get("title"),
                "original_title": movie.get("original_title"),
                "release_date": movie.get("release_date"),
                "original_language": movie.get("original_language"),
                "genre_ids": movie.get("genre_ids"),
                "popularity": movie.get("popularity"),
                "vote_average": movie.get("vote_average"),
                "vote_count": movie.get("vote_count"),
                "adult": movie.get("adult"),
                "overview": movie.get("overview"),
                "source_page": page,
                "ingestion_timestamp": ingestion_timestamp
            })

    key = (
        f"{PREFIX}/"
        f"year={now.year}/"
        f"month={now.month:02d}/"
        f"day={now.day:02d}/"
        f"data_{now.strftime('%Y-%m-%dT%H-%M-%S')}.json"
    )

    # NDJSON: una película por línea
    body = "\n".join([
        json.dumps(movie, ensure_ascii=False)
        for movie in movies_clean
    ])

    s3.put_object(
        Bucket=BUCKET,
        Key=key,
        Body=body.encode("utf-8"),
        ContentType="application/json"
    )

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Success",
            "pages_processed": 5,
            "records": len(movies_clean),
            "s3_path": f"s3://{BUCKET}/{key}",
            "ingestion_timestamp": ingestion_timestamp
        })
    }


def lambda_handler(event, context):
    """
    AWS Lambda entry point for the TMDb to Bronze ingestion process.
    
    Args:
        event (dict): The event dictionary containing the triggering data.
        context (LambdaContext): The runtime information of the Lambda function.
        
    Returns:
        dict: The result of the fetch_and_load execution.
    """
    return fetch_and_load()
