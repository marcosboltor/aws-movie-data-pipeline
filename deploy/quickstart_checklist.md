# Quick Deployment Checklist

Use this checklist to replicate the project quickly.

## 1. Deploy infrastructure

```bash
aws cloudformation deploy \
  --template-file iac/cloudformation_tmdb_datalake.yml \
  --stack-name streamsight-tmdb-dev \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    TmdbApiKey=YOUR_TMDB_API_KEY \
    DataLakeBucketName=YOUR_UNIQUE_BUCKET_NAME
```

## 2. Upload real Lambda code

Replace the placeholder code in:

- `tmdb_to_bronze`
- `bronce_tmdb_to_silver`
- `silver_tmdb_to_gold`

with the files from:

```text
src/lambdas/
```

## 3. Test Bronze

Run:

```text
tmdb_to_bronze
```

Expected result:

```text
1bronce/tmdb/popular/
```

contains a new `.json` file.

## 4. Test Silver

Confirm that the S3 event triggers:

```text
bronce_tmdb_to_silver
```

Expected result:

```text
2silver/movies/
```

contains Parquet files.

## 5. Run Glue Crawler

Run:

```text
crawler-movies-silver
```

Expected result:

```text
db_movies_tmdb.2silver
```

exists in Glue/Athena.

## 6. Test Gold

Run or wait for:

```text
silver_tmdb_to_gold
```

Expected Gold tables:

```text
gold_performance_genero
gold_ranking_peliculas
gold_peliculas_sobreexpuestas
gold_tendencia_generos
```

## 7. Validate Athena

Run:

```sql
SHOW TABLES IN db_movies_tmdb;
```

Then query any Gold table.

## 8. Connect Power BI

Use ODBC Athena connection and query the Gold tables from:

```text
db_movies_tmdb
```

