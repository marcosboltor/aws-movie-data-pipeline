# Glue Crawler Configuration

## Crawler name

crawler-movies-silver

## Purpose

This crawler detects the schema and partitions of the Silver layer stored in Amazon S3.

Its purpose is to keep the AWS Glue Data Catalog updated so Amazon Athena can query the Silver data as a SQL table.

In this project, AWS Glue is used only for metadata cataloging. It is not used as an ETL engine. Data transformation is performed by AWS Lambda and Amazon Athena.

## AWS Glue database

db_movies_tmdb

## Data source

Amazon S3

## S3 target path

s3://unam-2026-ingenieriadatos-equipo1-997622531618-us-east-2-an/2silver/

## Output table

2silver

## File format

Parquet

## Crawler state

READY

## Recrawl behavior

Recrawl all

## Schedule

On demand.

The crawler is executed manually when the Silver schema or partitions need to be refreshed in the Glue Data Catalog.

## IAM role

AWSGlueServiceRole-read-silver

## IAM role purpose

The IAM role allows AWS Glue to read the Silver layer in Amazon S3 and update the Glue Data Catalog metadata.

## IAM scope

The role has limited access to the project bucket and the Silver prefix.

Bucket:
unam-2026-ingenieriadatos-equipo1-997622531618-us-east-2-an

Allowed S3 path:
2silver/*

AWS account:
997622531618

## Security configuration

No additional security configuration was assigned.

## Lake Formation configuration

No Lake Formation configuration was used.

## Table prefix

No table prefix was configured.

## Notes

The crawler should remain focused on the Silver layer because the Gold tables are created directly by Athena CTAS queries from the silver_tmdb_to_gold Lambda.

Some additional tables may appear in Glue if the crawler detects individual files or intermediate partition folders as separate datasets. These tables are not part of the final data model and should not be used for business analysis.

Ignored tables:

- 23bf1f627cf741529b801c552fd8f488_snappy_parquet
- 50ab8e2b8eaa468984596f563b7c2ec4_snappy_parquet
- month_05

Valid tables:

- 2silver
- gold_performance_genero
- gold_ranking_peliculas
- gold_peliculas_sobreexpuestas
- gold_tendencia_generos
