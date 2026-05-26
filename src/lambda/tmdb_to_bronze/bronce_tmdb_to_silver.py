import json
import boto3
import pandas as pd
import awswrangler as wr
import urllib.parse
from datetime import datetime, timezone

s3 = boto3.client("s3")
lambda_client = boto3.client("lambda")

GENRE_MAP = {
    28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy",
    80: "Crime", 99: "Documentary", 18: "Drama", 10751: "Family",
    14: "Fantasy", 36: "History", 27: "Horror", 10402: "Music",
    9648: "Mystery", 10749: "Romance", 878: "Science Fiction",
    10770: "TV Movie", 53: "Thriller", 10752: "War", 37: "Western"
}

BUCKET_NAME = "unam-2026-ingenieriadatos-equipo1-997622531618-us-east-2-an"
SILVER_PREFIX = "2silver/movies"
GOLD_LAMBDA_NAME = "silver_tmdb_to_gold"


def load_bronze_data(bucket, key):
    """
    Loads raw NDJSON movie data from the Bronze S3 bucket into a pandas DataFrame.
    
    Args:
        bucket (str): The name of the S3 bucket containing the Bronze data.
        key (str): The object key (path) of the file in the bucket.
        
    Returns:
        pd.DataFrame: A DataFrame containing the parsed raw data.
    """
    response = s3.get_object(Bucket=bucket, Key=key)
    content = response["Body"].read().decode("utf-8")

    data = []

    for line in content.splitlines():
        line = line.strip()

        if not line:
            continue

        if line.endswith(","):
            line = line[:-1]

        data.append(json.loads(line))

    return pd.DataFrame(data)


def clean_data(df):
    """
    Cleans and standardizes the Bronze DataFrame by filtering columns, mapping genre IDs 
    to names, formatting dates, and calculating derived scores.
    
    Args:
        df (pd.DataFrame): The raw DataFrame from the Bronze layer.
        
    Returns:
        pd.DataFrame: The cleaned and normalized DataFrame.
    """
    cols_to_keep = [
        "id",
        "title",
        "original_title",
        "release_date",
        "original_language",
        "genre_ids",
        "popularity",
        "vote_average",
        "vote_count",
        "adult",
        "overview",
        "source_page",
        "ingestion_timestamp"
    ]

    cols_present = [col for col in cols_to_keep if col in df.columns]
    df_clean = df[cols_present].copy()

    def map_genres(genre_list):
        if not isinstance(genre_list, list):
            return "Unknown"

        return ", ".join([
            GENRE_MAP.get(g, "Unknown")
            for g in genre_list
        ])

    if "genre_ids" in df_clean.columns:
        df_clean["genres"] = df_clean["genre_ids"].apply(map_genres)
        df_clean = df_clean.drop(columns=["genre_ids"])

    if "release_date" in df_clean.columns:
        df_clean["release_date"] = pd.to_datetime(
            df_clean["release_date"],
            format="mixed",
            errors="coerce"
        )

    if "ingestion_timestamp" in df_clean.columns:
        df_clean["ingestion_timestamp"] = pd.to_datetime(
            df_clean["ingestion_timestamp"],
            format="mixed",
            errors="coerce"
        )
        df_clean["ingestion_date"] = df_clean["ingestion_timestamp"].dt.date

    if "vote_average" in df_clean.columns:
        df_clean["audience_score"] = (
            df_clean["vote_average"] * 10
        ).fillna(0).astype(int)

    return df_clean


def apply_data_quality(df):
    """
    Applies data quality filters, keeping only movies with 100 or more votes, 
    removing null IDs and titles, and deduplicating by ID.
    
    Args:
        df (pd.DataFrame): The cleaned DataFrame.
        
    Returns:
        pd.DataFrame: The final DataFrame that passes all quality checks.
    """
    if "vote_count" in df.columns:
        df_quality = df[df["vote_count"] >= 100].copy()
    else:
        df_quality = df.copy()

    df_quality = df_quality.dropna(subset=["id", "title"])
    df_quality = df_quality.drop_duplicates(subset=["id"])

    return df_quality


def save_silver_parquet(df):
    """
    Saves the cleaned and filtered DataFrame to the Silver layer in S3 as a Parquet file 
    partitioned by year, month, and day.
    
    Args:
        df (pd.DataFrame): The finalized DataFrame to be saved.
        
    Returns:
        str: The S3 path where the Parquet data was saved.
    """
    now = datetime.now(timezone.utc)

    s3_path = (
        f"s3://{BUCKET_NAME}/{SILVER_PREFIX}/"
        f"year={now.year}/"
        f"month={now.month:02d}/"
        f"day={now.day:02d}/"
    )

    wr.s3.to_parquet(
        df=df,
        path=s3_path,
        index=False,
        dataset=True,
        mode="append"
    )

    return s3_path


def invoke_gold_lambda(source_key, output_path, records_processed):
    """
    Asynchronously invokes the Gold layer Lambda function after the Silver processing 
    completes successfully. Uses InvocationType='Event' so Silver doesn't wait for Gold.
    
    Args:
        source_key (str): The original Bronze file key that triggered this process.
        output_path (str): The S3 path where the Silver Parquet file was saved.
        records_processed (int): The number of valid records saved to Silver.
        
    Returns:
        dict: The response from the Lambda invocation call.
    """
    payload = {
        "triggered_by": "bronce_tmdb_to_silver",
        "source_file": source_key,
        "silver_output_path": output_path,
        "records_processed": records_processed
    }

    response = lambda_client.invoke(
        FunctionName=GOLD_LAMBDA_NAME,
        InvocationType="Event",
        Payload=json.dumps(payload).encode("utf-8")
    )

    print(f"Lambda Gold invocada correctamente. StatusCode: {response.get('StatusCode')}")

    return response


def lambda_handler(event, context):
    """
    AWS Lambda entry point for the Bronze to Silver ETL process.
    Triggered by S3 events, it loads the raw data, cleans it, applies quality rules, 
    saves the result to Silver as Parquet, and triggers the Gold Lambda.
    
    Args:
        event (dict): The S3 event dictionary.
        context (LambdaContext): The runtime information of the Lambda function.
        
    Returns:
        dict: An HTTP-like response containing execution results.
    """
    try:
        source_bucket = event["Records"][0]["s3"]["bucket"]["name"]
        source_key = urllib.parse.unquote_plus(
            event["Records"][0]["s3"]["object"]["key"],
            encoding="utf-8"
        )

        print(f"Evento detectado. Procesando archivo: {source_key}")

        if not source_key.startswith("1bronce/tmdb/popular/"):
            print("Archivo ignorado: no pertenece a bronze/tmdb/popular.")
            return {
                "statusCode": 200,
                "body": "Archivo ignorado por prefijo."
            }

        df_raw = load_bronze_data(source_bucket, source_key)
        df_clean = clean_data(df_raw)
        df_final = apply_data_quality(df_clean)

        if df_final.empty:
            print("Ninguna película superó los filtros de calidad.")
            return {
                "statusCode": 200,
                "body": "Sin datos válidos."
            }

        output_path = save_silver_parquet(df_final)

        print(f"Éxito. Parquet generado en: {output_path}")

        invoke_gold_lambda(
            source_key=source_key,
            output_path=output_path,
            records_processed=len(df_final)
        )

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Capa Silver procesada exitosamente y Gold invocada",
                "source_file": source_key,
                "records_processed": len(df_final),
                "output_path": output_path
            })
        }

    except Exception as e:
        print(f"Error procesando el pipeline: {str(e)}")
        raise e