# Glue Data Catalog Schema

## Database

db_movies_tmdb

## Purpose

The db_movies_tmdb database stores the metadata definitions required by Amazon Athena to query the Silver and Gold layers of the Data Lake.

The Silver table is detected by AWS Glue Crawler from Parquet files stored in Amazon S3.

The Gold tables are created by Athena CTAS queries executed from the silver_tmdb_to_gold Lambda.

## Valid tables

The final analytical model uses the following tables:

- 2silver
- gold_performance_genero
- gold_ranking_peliculas
- gold_peliculas_sobreexpuestas
- gold_tendencia_generos

## Ignored tables

The following tables were detected by the crawler but are not part of the final model:

- 23bf1f627cf741529b801c552fd8f488_snappy_parquet
- 50ab8e2b8eaa468984596f563b7c2ec4_snappy_parquet
- month_05

These tables should be ignored because they correspond to individual Parquet files or intermediate partition folders, not to business-ready datasets.

---

# Table: 2silver

## Layer

Silver

## Description

Cleaned and structured movie data stored in Parquet format.

This table contains movie records extracted from TMDb, transformed by the bronce_tmdb_to_silver Lambda and registered in the Glue Data Catalog for Athena queries.

## Location

s3://unam-2026-ingenieriadatos-equipo1-997622531618-us-east-2-an/2silver/

## Classification

Parquet

## Columns

| Column name | Data type | Description |
|---|---|---|
| id | bigint | TMDb movie identifier. |
| title | string | Movie title. |
| release_date | timestamp | Movie release date. |
| popularity | double | TMDb popularity score. |
| vote_average | double | Average user rating. |
| vote_count | bigint | Number of votes received by the movie. |
| genres | string | Movie genres mapped from TMDb genre identifiers. |
| audience_score | bigint | Vote average transformed to a 0-100 scale. |
| original_title | string | Original movie title. |
| original_language | string | Original language of the movie. |
| adult | boolean | Indicates whether the movie is classified as adult content. |
| overview | string | Movie overview or synopsis. |
| source_page | int | TMDb API page from which the record was extracted. |
| ingestion_timestamp | timestamp | Timestamp when the record was ingested into the pipeline. |
| ingestion_date | date | Date derived from the ingestion timestamp. |

## Partitions

| Partition column | Data type | Description |
|---|---|---|
| partition_0 | string | Partition detected by Glue due to the S3 folder structure. |
| year | string | Year partition. |

## Notes

The Silver table preserves cleaned historical data. The Gold layer later selects the most recent record per movie using ingestion_timestamp.

---

# Table: gold_performance_genero

## Layer

Gold

## Description

Analytical table used to identify movie genres with the best recent performance based on popularity, rating and voting volume.

## Business question

What genres have the best recent performance?

## Location

s3://unam-2026-ingenieriadatos-equipo1-997622531618-us-east-2-an/3gold/performance_genero/

## Columns

| Column name | Data type | Description |
|---|---|---|
| genre | string | Movie genre. |
| total_peliculas | bigint | Number of movies associated with the genre. |
| popularidad_promedio | double | Average popularity for the genre. |
| popularidad_maxima | double | Maximum popularity observed for the genre. |
| calificacion_promedio | double | Average rating for the genre. |
| votos_promedio | double | Average vote count for the genre. |
| score_desempeno | double | Composite performance score based on popularity, rating and vote count. |

---

# Table: gold_ranking_peliculas

## Layer

Gold

## Description

Analytical table used to rank movies that are good candidates for recommendation or promotion.

## Business question

Which movies should be recommended or promoted?

## Location

s3://unam-2026-ingenieriadatos-equipo1-997622531618-us-east-2-an/3gold/ranking_peliculas/

## Columns

| Column name | Data type | Description |
|---|---|---|
| id | bigint | TMDb movie identifier. |
| title | string | Movie title. |
| genres | string | Movie genres. |
| release_date | timestamp | Movie release date. |
| original_language | string | Original language of the movie. |
| popularity | double | TMDb popularity score. |
| vote_average | double | Average user rating. |
| vote_count | bigint | Number of votes received by the movie. |
| ingestion_timestamp | timestamp | Timestamp of the latest selected record. |
| score_recomendacion | double | Composite recommendation score based on popularity, rating and vote count. |

---

# Table: gold_peliculas_sobreexpuestas

## Layer

Gold

## Description

Analytical table used to detect movies with high popularity but relatively low rating.

## Business question

Which movies are popular but have low ratings?

## Location

s3://unam-2026-ingenieriadatos-equipo1-997622531618-us-east-2-an/3gold/peliculas_sobreexpuestas/

## Columns

| Column name | Data type | Description |
|---|---|---|
| id | bigint | TMDb movie identifier. |
| title | string | Movie title. |
| genres | string | Movie genres. |
| release_date | timestamp | Movie release date. |
| popularity | double | TMDb popularity score. |
| vote_average | double | Average user rating. |
| vote_count | bigint | Number of votes received by the movie. |
| ingestion_timestamp | timestamp | Timestamp of the latest selected record. |

---

# Table: gold_tendencia_generos

## Layer

Gold

## Description

Analytical table used to identify genres with recent popularity growth.

## Business question

Which genres are growing in popularity?

## Location

s3://unam-2026-ingenieriadatos-equipo1-997622531618-us-east-2-an/3gold/tendencia_generos/

## Columns

| Column name | Data type | Description |
|---|---|---|
| genre | string | Movie genre. |
| popularidad_inicial | double | Initial average popularity in the analysis window. |
| popularidad_reciente | double | Most recent average popularity in the analysis window. |
| cambio_popularidad | double | Difference between recent and initial popularity. |
| dias_observados | bigint | Number of observed ingestion dates for the genre. |

---

# Cataloging notes

The Gold tables are created by Athena CTAS queries. Therefore, their metadata is registered in the Glue Data Catalog through Athena.

The Silver table is maintained through the Glue Crawler because its files are written directly to S3 in Parquet format by the Silver Lambda.
