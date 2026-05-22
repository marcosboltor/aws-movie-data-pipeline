import boto3
import time

athena_client = boto3.client("athena")
s3_client = boto3.client("s3")

DATABASE = "db_movies_tmdb"
OUTPUT_ATHENA = "s3://unam-2026-ingenieriadatos-equipo1-997622531618-us-east-2-an/athena/"

BUCKET_NAME = "unam-2026-ingenieriadatos-equipo1-997622531618-us-east-2-an"
GOLD_BASE_PATH = "s3://unam-2026-ingenieriadatos-equipo1-997622531618-us-east-2-an/3gold"

GOLD_PREFIXES = [
    "3gold/performance_genero/",
    "3gold/ranking_peliculas/",
    "3gold/peliculas_sobreexpuestas/",
    "3gold/tendencia_generos/"
]


def wait_for_query(query_execution_id):
    """
    Polls the Athena query execution status until it succeeds, fails, or is cancelled.
    
    Args:
        query_execution_id (str): The execution ID of the Athena query to monitor.
        
    Raises:
        Exception: If the query fails or is cancelled, raises an exception with the failure reason.
    """
    while True:
        response = athena_client.get_query_execution(
            QueryExecutionId=query_execution_id
        )

        status = response["QueryExecution"]["Status"]["State"]

        if status in ["SUCCEEDED", "FAILED", "CANCELLED"]:
            break

        time.sleep(2)

    if status != "SUCCEEDED":
        reason = response["QueryExecution"]["Status"].get(
            "StateChangeReason",
            "Sin detalle del error"
        )
        raise Exception(f"Query falló con estado {status}: {reason}")


def run_query(query):
    """
    Executes an Athena query and waits for its completion.
    
    Args:
        query (str): The SQL query string to be executed in Athena.
    """
    response = athena_client.start_query_execution(
        QueryString=query,
        QueryExecutionContext={"Database": DATABASE},
        ResultConfiguration={"OutputLocation": OUTPUT_ATHENA}
    )

    query_execution_id = response["QueryExecutionId"]
    wait_for_query(query_execution_id)


def clean_s3_prefix(bucket, prefix):
    """
    Deletes all objects within a specific S3 prefix.
    This prevents HIVE_PATH_ALREADY_EXISTS errors when recreating CTAS tables.
    
    Args:
        bucket (str): The name of the S3 bucket.
        prefix (str): The prefix (folder path) to clean up.
    """
    print(f"Limpiando s3://{bucket}/{prefix}")

    paginator = s3_client.get_paginator("list_objects_v2")
    pages = paginator.paginate(Bucket=bucket, Prefix=prefix)

    objects_to_delete = []

    for page in pages:
        for obj in page.get("Contents", []):
            objects_to_delete.append({"Key": obj["Key"]})

            if len(objects_to_delete) == 1000:
                s3_client.delete_objects(
                    Bucket=bucket,
                    Delete={"Objects": objects_to_delete}
                )
                objects_to_delete = []

    if objects_to_delete:
        s3_client.delete_objects(
            Bucket=bucket,
            Delete={"Objects": objects_to_delete}
        )

    print(f"Prefijo limpiado: s3://{bucket}/{prefix}")


def lambda_handler(event, context):
    """
    AWS Lambda entry point for the Silver to Gold transformation process.
    It drops existing Gold tables, cleans up S3 folders, and regenerates 
    the analytical Gold tables via Athena CTAS queries.
    
    Args:
        event (dict): The event dictionary containing the triggering data.
        context (LambdaContext): The runtime information of the Lambda function.
        
    Returns:
        dict: A response dictionary indicating the successful update of the Gold layer.
    """
    print("Iniciando actualización de capa Gold")
    print(f"Evento recibido: {event}")

    # =========================
    # 1. Eliminar tablas Gold del catálogo
    # =========================

    drop_queries = [
        f"DROP TABLE IF EXISTS {DATABASE}.gold_performance_genero",
        f"DROP TABLE IF EXISTS {DATABASE}.gold_ranking_peliculas",
        f"DROP TABLE IF EXISTS {DATABASE}.gold_peliculas_sobreexpuestas",
        f"DROP TABLE IF EXISTS {DATABASE}.gold_tendencia_generos",
        f"DROP TABLE IF EXISTS {DATABASE}.gold_metricas_por_genero"
    ]

    for query in drop_queries:
        run_query(query)

    # =========================
    # 2. Limpiar carpetas físicas de Gold en S3
    # =========================

    for prefix in GOLD_PREFIXES:
        clean_s3_prefix(BUCKET_NAME, prefix)

    # =========================
    # 3. Crear gold_performance_genero
    # =========================

    run_query(f"""
    CREATE TABLE {DATABASE}.gold_performance_genero
    WITH (
        format = 'PARQUET',
        external_location = '{GOLD_BASE_PATH}/performance_genero/'
    ) AS
    WITH recent_movies AS (
        SELECT *
        FROM "2silver"
        WHERE vote_count >= 100
          AND ingestion_timestamp >= current_timestamp - interval '30' day
    ),
    latest_movies AS (
        SELECT *
        FROM (
            SELECT
                *,
                ROW_NUMBER() OVER (
                    PARTITION BY id
                    ORDER BY ingestion_timestamp DESC
                ) AS rn
            FROM recent_movies
        )
        WHERE rn = 1
    ),
    movies_by_genre AS (
        SELECT
            id,
            title,
            TRIM(genre) AS genre,
            popularity,
            vote_average,
            vote_count
        FROM latest_movies
        CROSS JOIN UNNEST(split(genres, ',')) AS t(genre)
    )
    SELECT
        genre,
        COUNT(DISTINCT id) AS total_peliculas,
        ROUND(AVG(popularity), 2) AS popularidad_promedio,
        ROUND(MAX(popularity), 2) AS popularidad_maxima,
        ROUND(AVG(vote_average), 2) AS calificacion_promedio,
        ROUND(AVG(vote_count), 2) AS votos_promedio,
        ROUND(
            AVG(popularity) * 0.4 +
            AVG(vote_average) * 10 * 0.4 +
            AVG(vote_count) / 100 * 0.2,
            2
        ) AS score_desempeno
    FROM movies_by_genre
    GROUP BY genre
    """)

    # =========================
    # 4. Crear gold_ranking_peliculas
    # =========================

    run_query(f"""
    CREATE TABLE {DATABASE}.gold_ranking_peliculas
    WITH (
        format = 'PARQUET',
        external_location = '{GOLD_BASE_PATH}/ranking_peliculas/'
    ) AS
    WITH recent_movies AS (
        SELECT *
        FROM "2silver"
        WHERE vote_count >= 100
          AND ingestion_timestamp >= current_timestamp - interval '30' day
    ),
    latest_movies AS (
        SELECT *
        FROM (
            SELECT
                *,
                ROW_NUMBER() OVER (
                    PARTITION BY id
                    ORDER BY ingestion_timestamp DESC
                ) AS rn
            FROM recent_movies
        )
        WHERE rn = 1
    )
    SELECT
        id,
        title,
        genres,
        release_date,
        original_language,
        popularity,
        vote_average,
        vote_count,
        ingestion_timestamp,
        ROUND(
            popularity * 0.4 +
            vote_average * 10 * 0.4 +
            vote_count / 100 * 0.2,
            2
        ) AS score_recomendacion
    FROM latest_movies
    """)

    # =========================
    # 5. Crear gold_peliculas_sobreexpuestas
    # =========================

    run_query(f"""
    CREATE TABLE {DATABASE}.gold_peliculas_sobreexpuestas
    WITH (
        format = 'PARQUET',
        external_location = '{GOLD_BASE_PATH}/peliculas_sobreexpuestas/'
    ) AS
    WITH recent_movies AS (
        SELECT *
        FROM "2silver"
        WHERE vote_count >= 100
          AND ingestion_timestamp >= current_timestamp - interval '30' day
    ),
    latest_movies AS (
        SELECT *
        FROM (
            SELECT
                *,
                ROW_NUMBER() OVER (
                    PARTITION BY id
                    ORDER BY ingestion_timestamp DESC
                ) AS rn
            FROM recent_movies
        )
        WHERE rn = 1
    ),
    global_metrics AS (
        SELECT
            AVG(popularity) AS avg_popularity,
            AVG(vote_average) AS avg_vote_average
        FROM latest_movies
    )
    SELECT
        m.id,
        m.title,
        m.genres,
        m.release_date,
        m.popularity,
        m.vote_average,
        m.vote_count,
        m.ingestion_timestamp
    FROM latest_movies m
    CROSS JOIN global_metrics g
    WHERE m.popularity > g.avg_popularity
      AND m.vote_average < g.avg_vote_average
    """)

    # =========================
    # 6. Crear gold_tendencia_generos
    # =========================

    run_query(f"""
    CREATE TABLE {DATABASE}.gold_tendencia_generos
    WITH (
        format = 'PARQUET',
        external_location = '{GOLD_BASE_PATH}/tendencia_generos/'
    ) AS
    WITH recent_movies AS (
        SELECT *
        FROM "2silver"
        WHERE vote_count >= 100
          AND ingestion_timestamp >= current_timestamp - interval '30' day
    ),
    movies_by_genre AS (
        SELECT
            id,
            title,
            TRIM(genre) AS genre,
            popularity,
            vote_average,
            vote_count,
            ingestion_timestamp
        FROM recent_movies
        CROSS JOIN UNNEST(split(genres, ',')) AS t(genre)
    ),
    genre_by_day AS (
        SELECT
            genre,
            DATE(ingestion_timestamp) AS ingestion_date,
            ROUND(AVG(popularity), 2) AS popularidad_promedio_dia
        FROM movies_by_genre
        GROUP BY genre, DATE(ingestion_timestamp)
    ),
    genre_trend AS (
        SELECT
            genre,
            MIN_BY(popularidad_promedio_dia, ingestion_date) AS popularidad_inicial,
            MAX_BY(popularidad_promedio_dia, ingestion_date) AS popularidad_reciente,
            COUNT(DISTINCT ingestion_date) AS dias_observados
        FROM genre_by_day
        GROUP BY genre
    )
    SELECT
        genre,
        popularidad_inicial,
        popularidad_reciente,
        ROUND(popularidad_reciente - popularidad_inicial, 2) AS cambio_popularidad,
        dias_observados
    FROM genre_trend
    WHERE dias_observados >= 2
    """)

    return {
        "statusCode": 200,
        "body": "Capa Gold actualizada correctamente de forma automática."
    }