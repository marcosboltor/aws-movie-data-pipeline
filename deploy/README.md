# Deployment Guide

This guide explains how to replicate the StreamSight TMDb Analytics project in AWS.

The project implements a serverless data lake for movie catalog analytics using TMDb data. The pipeline follows a Bronze, Silver and Gold architecture and exposes the final analytical tables through Amazon Athena and Power BI.

## 1. Project architecture

The deployment creates or configures the following components:

- Amazon S3 data lake bucket.
- Bronze layer for raw TMDb data.
- Silver layer for cleaned Parquet data.
- Gold layer for analytical tables.
- AWS Lambda functions for ingestion and transformation.
- Amazon EventBridge Scheduler for automated ingestion.
- S3 Event Notification for Bronze to Silver processing.
- AWS Glue Data Catalog and Glue Crawler.
- Amazon Athena for SQL queries and CTAS Gold table creation.
- AWS Secrets Manager for TMDb API configuration.
- Power BI Desktop connection through ODBC to Athena.

The general flow is:

```text
TMDb API
→ EventBridge Scheduler
→ Lambda tmdb_to_bronze
→ S3 Bronze
→ S3 Event Notification
→ Lambda bronce_tmdb_to_silver
→ S3 Silver
→ Lambda silver_tmdb_to_gold
→ Athena CTAS
→ S3 Gold
→ Power BI Desktop
```

## 2. Prerequisites

Before deploying the project, make sure you have:

- An AWS account.
- AWS CLI configured locally.
- Python 3.11 or compatible runtime.
- A TMDb API key.
- Permissions to create or manage:
  - S3 buckets
  - Lambda functions
  - IAM roles and policies
  - EventBridge Scheduler
  - Secrets Manager secrets
  - Glue databases and crawlers
  - Athena workgroups and queries
- Power BI Desktop installed.
- Amazon Athena ODBC driver installed if the dashboard will be replicated.

## 3. Suggested repository structure

Use the following structure in the repository:

```text
project-root/
├── docs/
├── img/
├── iac/
│   ├── cloudformation_tmdb_datalake.yml
│   └── README.md
├── deploy/
│   └── README.md
├── src/
│   ├── lambdas/
│   │   ├── tmdb_to_bronze/
│   │   ├── bronce_tmdb_to_silver/
│   │   └── silver_tmdb_to_gold/
│   ├── athena/
│   ├── glue/
│   ├── powerbi/
│   └── config/
└── README.md
```

## 4. Infrastructure deployment

The infrastructure can be deployed using the CloudFormation template located in:

```text
iac/cloudformation_tmdb_datalake.yml
```

Run the following command from the root of the repository:

```bash
aws cloudformation deploy \
  --template-file iac/cloudformation_tmdb_datalake.yml \
  --stack-name streamsight-tmdb-dev \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    TmdbApiKey=YOUR_TMDB_API_KEY \
    DataLakeBucketName=YOUR_UNIQUE_BUCKET_NAME
```

Replace:

```text
YOUR_TMDB_API_KEY
```

with your TMDb API key.

Replace:

```text
YOUR_UNIQUE_BUCKET_NAME
```

with a globally unique S3 bucket name.

Important: if the bucket already exists in AWS and was created manually, CloudFormation may fail when trying to create it again. In that case, either use a different bucket name or adapt the template to reference the existing bucket.

## 5. S3 folder structure

After the bucket is created, the project uses the following logical prefixes:

```text
1bronce/tmdb/popular/
2silver/movies/
3gold/performance_genero/
3gold/ranking_peliculas/
3gold/peliculas_sobreexpuestas/
3gold/tendencia_generos/
athena/
```

Expected purpose:

- `1bronce/`: raw NDJSON files from TMDb.
- `2silver/`: cleaned and structured Parquet files.
- `3gold/`: analytical tables generated with Athena CTAS.
- `athena/`: Athena query result output location.

## 6. Secrets Manager configuration

The Bronze Lambda reads its configuration from AWS Secrets Manager.

The secret should contain:

```json
{
  "TMDB_API_KEY": "YOUR_TMDB_API_KEY",
  "TMDB_BASE_URL": "https://api.themoviedb.org/3",
  "TMDB_ENDPOINT": "/movie/popular",
  "S3_BUCKET": "YOUR_BUCKET_NAME",
  "S3_PREFIX": "1bronce/tmdb/popular/"
}
```

Do not commit real API keys or AWS credentials to the repository.

## 7. Lambda deployment

The CloudFormation template creates the Lambda functions with placeholder code.

After the infrastructure is deployed, replace the placeholder code with the real implementation from:

```text
src/lambdas/tmdb_to_bronze/lambda_function.py
src/lambdas/bronce_tmdb_to_silver/lambda_function.py
src/lambdas/silver_tmdb_to_gold/lambda_function.py
```

The expected Lambda functions are:

```text
tmdb_to_bronze
bronce_tmdb_to_silver
silver_tmdb_to_gold
```

### 7.1 tmdb_to_bronze

Purpose:

- Read configuration from Secrets Manager.
- Query TMDb `/movie/popular`.
- Retrieve 5 pages per execution.
- Add metadata such as `source_page` and `ingestion_timestamp`.
- Write raw NDJSON files to S3 Bronze.

Expected output:

```text
s3://YOUR_BUCKET_NAME/1bronce/tmdb/popular/year=YYYY/month=MM/day=DD/data_TIMESTAMP.json
```

### 7.2 bronce_tmdb_to_silver

Purpose:

- Trigger automatically when a new Bronze file is created.
- Read raw NDJSON data.
- Clean and transform the dataset.
- Map TMDb genre IDs to genre names.
- Convert dates and timestamps.
- Filter low-quality records.
- Write Parquet files to the Silver layer.
- Invoke the Gold Lambda.

Expected output:

```text
s3://YOUR_BUCKET_NAME/2silver/movies/year=YYYY/month=MM/day=DD/
```

### 7.3 silver_tmdb_to_gold

Purpose:

- Create analytical Gold tables using Athena CTAS.
- Drop previous Gold tables.
- Clean previous S3 Gold paths.
- Generate the final business tables.

Expected output:

```text
s3://YOUR_BUCKET_NAME/3gold/
```

Gold tables:

```text
gold_performance_genero
gold_ranking_peliculas
gold_peliculas_sobreexpuestas
gold_tendencia_generos
```

## 8. EventBridge Scheduler

The ingestion Lambda should be executed automatically using EventBridge Scheduler.

Recommended schedule:

```text
Monday and Friday at 08:00 America/Mexico_City
```

CloudFormation default expression:

```text
cron(0 8 ? * MON,FRI *)
```

Target Lambda:

```text
tmdb_to_bronze
```

## 9. S3 Event Notification

The Bronze to Silver process is triggered by S3.

Configuration:

```text
Bucket: YOUR_BUCKET_NAME
Event type: ObjectCreated
Prefix: 1bronce/tmdb/popular/
Suffix: .json
Destination: Lambda bronce_tmdb_to_silver
```

This allows the Silver layer to run automatically when the Bronze layer receives a new file.

## 10. Glue Data Catalog and Crawler

The project uses Glue as the metadata catalog.

Database:

```text
db_movies_tmdb
```

Crawler:

```text
crawler-movies-silver
```

Crawler target:

```text
s3://YOUR_BUCKET_NAME/2silver/
```

Expected Silver table:

```text
2silver
```

After the Silver layer writes Parquet files, run the crawler to update the Data Catalog.

## 11. Athena validation

Use Athena to validate the Silver and Gold tables.

Database:

```text
db_movies_tmdb
```

Suggested validation queries:

```sql
SHOW TABLES IN db_movies_tmdb;
```

```sql
DESCRIBE `2silver`;
```

```sql
SELECT *
FROM "2silver"
LIMIT 10;
```

```sql
SELECT *
FROM gold_performance_genero
ORDER BY score_desempeno DESC;
```

```sql
SELECT *
FROM gold_ranking_peliculas
ORDER BY score_recomendacion DESC
LIMIT 10;
```

```sql
SELECT *
FROM gold_peliculas_sobreexpuestas
ORDER BY popularity DESC;
```

```sql
SELECT *
FROM gold_tendencia_generos
ORDER BY cambio_popularidad DESC;
```

## 12. Power BI connection

Power BI Desktop connects to Amazon Athena through the generic ODBC connector.

Recommended configuration:

```text
Driver: Amazon Athena ODBC 2.x
Authentication: IAM credentials
Region: us-east-2
Catalog: AwsDataCatalog
Database: db_movies_tmdb
Workgroup: primary or the project workgroup
Output location: s3://YOUR_BUCKET_NAME/athena/
```

Recommended queries for Power BI:

```sql
SELECT *
FROM db_movies_tmdb.gold_performance_genero
ORDER BY score_desempeno DESC;
```

```sql
SELECT *
FROM db_movies_tmdb.gold_ranking_peliculas
ORDER BY score_recomendacion DESC;
```

```sql
SELECT *
FROM db_movies_tmdb.gold_peliculas_sobreexpuestas
ORDER BY popularity DESC;
```

```sql
SELECT *
FROM db_movies_tmdb.gold_tendencia_generos
ORDER BY cambio_popularidad DESC;
```

The dashboard should include:

- KPIs for total movies, average rating, average popularity and total genres.
- Genre performance chart.
- Movie recommendation ranking.
- Overexposed movies table.
- Genre trend chart.

## 13. End-to-end validation checklist

Use this checklist to confirm that the project was replicated successfully.

### Infrastructure

- [ ] S3 bucket exists.
- [ ] Bronze, Silver, Gold and Athena prefixes exist or are created during execution.
- [ ] Secret exists in AWS Secrets Manager.
- [ ] Lambda functions exist.
- [ ] EventBridge Scheduler exists.
- [ ] S3 Event Notification is configured.
- [ ] Glue database exists.
- [ ] Glue crawler exists.
- [ ] Athena output location is configured.

### Pipeline execution

- [ ] EventBridge or manual test executes `tmdb_to_bronze`.
- [ ] Bronze file is created in S3.
- [ ] S3 event triggers `bronce_tmdb_to_silver`.
- [ ] Silver Parquet files are created.
- [ ] Silver Lambda invokes `silver_tmdb_to_gold`.
- [ ] Gold tables are created in Athena.
- [ ] Gold data is stored in S3.
- [ ] Athena queries return results.
- [ ] Power BI dashboard loads data from Athena.

## 14. Recommended screenshots for evidence

Save implementation screenshots under:

```text
img/screenshots/
```

Recommended minimum screenshots:

```text
aws_eventbridge_schedule.png
aws_lambda_functions.png
aws_s3_bronze.png
aws_s3_silver.png
aws_s3_gold.png
aws_glue_catalog_tables.png
aws_athena_gold_queries.png
powerbi_dashboard.png
```

These screenshots demonstrate that the project was implemented in AWS and connected to the visualization layer.

## 15. Common issues

### Bucket already exists

S3 bucket names are globally unique. If CloudFormation fails because the bucket already exists, use another bucket name or adapt the template to use an existing bucket.

### Lambda code is still placeholder

The CloudFormation template creates placeholder Lambdas. Replace the code with the real files from `src/lambdas/`.

### Athena cannot find columns

Run the Glue crawler again and verify that the Silver table schema includes the expected columns.

### Athena CTAS path already exists

If Athena returns `HIVE_PATH_ALREADY_EXISTS`, clean the corresponding S3 Gold folder and rerun the Gold Lambda.

### Power BI cannot connect to Athena

Verify:

- Athena ODBC driver is installed.
- Region is correct.
- Output S3 location is correct.
- IAM user has Athena, Glue and S3 read/query permissions.
- The selected database is `db_movies_tmdb`.

## 16. Cleanup

To remove the CloudFormation stack:

```bash
aws cloudformation delete-stack \
  --stack-name streamsight-tmdb-dev
```

Important: S3 buckets with existing objects may prevent stack deletion. Empty the bucket prefixes first if needed.

## 17. Security notes

- Do not store secrets in code.
- Do not commit AWS credentials.
- Use IAM least privilege where possible.
- Keep TMDb API credentials in Secrets Manager.
- Avoid public access to the S3 bucket.
- Use separate users or roles for Power BI access.
