# Technical Documentation  
# AWS/TMDb Pipeline for Streaming Catalog Analytics

**Client:** Streaming Platform  
**Project:** AWS/TMDb Data Lake for data-driven catalog management  
**Date:** May 2026  
**Version:** 2.0

---

## 1. Document Objective

This document describes the technical implementation of the data pipeline used by a streaming platform to analyze popular movie information from TMDb.

The solution transforms external data into Gold analytical tables that support decisions about genres, recommendable titles, overexposed content, and recent catalog trends.

---

## 2. General Technical Description

The pipeline is automated end to end using serverless and on-demand services. The flow starts with an EventBridge schedule, continues with ingestion from TMDb into Bronze, automatic transformation into Silver, and automatic generation of Gold tables through Athena CTAS. Finally, Power BI consumes Gold tables from Athena through ODBC.

Summary flow:

```text
TMDb API
↓
Amazon EventBridge Scheduler
↓
Lambda tmdb_to_bronze
↓
Amazon S3 - 1bronce/tmdb/popular/
↓ S3 Event Notification
Lambda bronce_tmdb_to_silver
↓
Amazon S3 - 2silver/movies/
↓ automatic invocation
Lambda silver_tmdb_to_gold
↓
Amazon Athena CTAS
↓
Amazon S3 - 3gold/
↓
Athena Query Editor / ODBC
↓
Power BI Desktop - Executive Dashboard
```

---

## 3. Services and Tools Used

| Service / Tool | Function in the Project |
|---|---|
| Amazon S3 | Main Data Lake. Stores Bronze, Silver, and Gold. |
| AWS Lambda | Runs ingestion, Silver transformation, and Gold generation. |
| Amazon EventBridge Scheduler | Schedules ingestion on Mondays and Fridays at 8:00 a.m. until the semester end date. |
| S3 Event Notification | Automatically triggers the Bronze-to-Silver Lambda when a new file is detected in Bronze. |
| AWS Glue Data Catalog | Metadata catalog used to query S3 files as tables. |
| AWS Glue Crawler | Detects schema and partitions in Silver; it does not transform data. |
| Amazon Athena | SQL engine used to validate data, create Gold tables through CTAS, and serve as the query source for Power BI. |
| AWS Secrets Manager | Stores the TMDb API Key and sensitive configuration. |
| IAM Roles | Controls permissions between Lambda, S3, Athena, and Glue. |
| Amazon EC2 | Development and testing environment; not part of the production pipeline. |
| Power BI Desktop | Visualization tool connected to Athena through ODBC. |
| Power BI Gateway / Power BI Service | Component prepared for scheduled refresh in production. |

---

## 4. Data Structure in S3

| Layer | Path | Description |
|---|---|---|
| Bronze | `1bronce/tmdb/popular/` | Raw TMDb data by ingestion date. |
| Silver | `2silver/movies/` | Clean, filtered data in Parquet; preserves clean history. |
| Gold | `3gold/` | Analytical tables for business questions. |
| Visualization | Power BI connected to Athena through ODBC | Executive dashboard consuming Gold tables. |

---

## 5. Ingestion Lambda: `tmdb_to_bronze`

### 5.1 Function

Extracts data from the TMDb API and stores it in S3 Bronze.

### 5.2 Input

- EventBridge schedule.
- Configuration from Secrets Manager.
- `/movie/popular` endpoint.
- Pages 1 to 5 per execution.

### 5.3 Output

- NDJSON file in:

```text
1bronce/tmdb/popular/
```

### 5.4 Added Metadata

- `source_page`
- `ingestion_timestamp`
- `ingestion_date`

### 5.5 Business Purpose

Preserve recent snapshots of the popular movie market to feed catalog analysis.

---

## 6. Transformation Lambda: `bronce_tmdb_to_silver`

### 6.1 Function

Cleans, filters, and normalizes raw Bronze data to generate a reliable Silver layer.

### 6.2 Activation

Automatically activated through S3 Event Notification when a new file arrives in Bronze.

### 6.3 Transformations

- Reading NDJSON files from Bronze.
- Selection of relevant columns.
- Genre mapping.
- Date conversion.
- Numeric metric conversion.
- Filtering movies with `vote_count >= 100`.
- Removal of duplicates within the batch.
- Preservation of ingestion metadata.
- Writing in Parquet format.

### 6.4 Output

```text
2silver/movies/
```

### 6.5 Main Fields

| Field | Description |
|---|---|
| `id` | TMDb movie identifier. |
| `title` | Movie title. |
| `original_title` | Original title. |
| `original_language` | Original language. |
| `release_date` | Release date. |
| `popularity` | TMDb popularity metric. |
| `vote_average` | Average rating. |
| `vote_count` | Number of votes. |
| `genres` | Genres associated with the movie. |
| `adult` | Adult content indicator. |
| `overview` | Movie overview. |
| `source_page` | Source page in TMDb. |
| `ingestion_timestamp` | Exact ingestion time. |
| `ingestion_date` | Ingestion date. |

---

## 7. Gold Generation Lambda: `silver_tmdb_to_gold`

### 7.1 Function

Generates Gold analytical tables for catalog decision-making.

### 7.2 Activation

Automatically invoked once the Silver transformation finishes successfully.

### 7.3 Process

- Drops previous Gold tables.
- Cleans S3 Gold folders.
- Executes Athena CTAS queries.
- Uses a 30-day rolling window.
- Selects the most recent record per movie using `ingestion_timestamp`.
- Splits multi-genre movies with `UNNEST(split(...))`.

### 7.4 Output

```text
3gold/
```

### 7.5 Gold Tables

| Table | Purpose |
|---|---|
| `gold_performance_genero` | Analyze recent performance by genre. |
| `gold_ranking_peliculas` | Prioritize recommendable or promotable movies. |
| `gold_peliculas_sobreexpuestas` | Detect popular movies with low ratings. |
| `gold_tendencia_generos` | Identify genres with recent growth. |

---

## 8. Implemented Business Rules

- Only movies with `vote_count >= 100` are considered.
- Gold uses a 30-day rolling window.
- If a movie appears multiple times, the most recent record is selected.
- A movie may belong to multiple genres.
- Genre analysis splits multiple genres with `UNNEST(split(...))`.
- The performance score combines popularity, rating, and vote volume.
- Bronze preserves raw snapshots.
- Silver preserves clean historical data.
- Gold represents a recent analytical market view.

---

## 9. Glue Data Catalog and Glue Crawler

### 9.1 Glue Crawler

The crawler detects the schema and partitions of Silver. Its function is to register data so it can be queried from Athena. It does not perform data transformation.

### 9.2 Glue Data Catalog

The catalog registers the project tables. The database used for querying is:

```text
db_movies_tmdb
```

Silver and Gold tables are queried from Athena through this database.

---

## 10. Athena

Athena performs two main functions:

1. Validate data and query tables.
2. Create Gold tables through CTAS.

Conceptual query example:

```sql
SELECT *
FROM db_movies_tmdb.gold_ranking_peliculas
LIMIT 10;
```

Conceptual validation example:

```sql
SELECT COUNT(*) AS total_movies
FROM db_movies_tmdb.gold_ranking_peliculas;
```

The exact queries must be stored in:

```text
src/athena/
```

---

## 11. Power BI

Power BI Desktop consumes Gold tables from Athena through a generic ODBC connection configured with the Amazon Athena driver and a DSN pointing to `db_movies_tmdb`.

### 11.1 Data Source

- `gold_performance_genero`
- `gold_ranking_peliculas`
- `gold_peliculas_sobreexpuestas`
- `gold_tendencia_generos`

### 11.2 Dashboard

The dashboard visualizes:

- General KPIs.
- Genre performance.
- Genre trends.
- Ranking of recommendable movies.
- Overexposed movies.

### 11.3 Refresh

In Power BI Desktop, refresh is executed manually with Refresh. In production, the report can be published to Power BI Service and refreshed through Power BI Gateway, aligned with the pipeline execution on Mondays and Fridays.

---

## 12. Automation

The pipeline uses three automation mechanisms:

| Mechanism | Use |
|---|---|
| EventBridge Scheduler | Runs ingestion on Mondays and Fridays at 8:00 a.m. |
| S3 Event Notification | Triggers Silver when a file arrives in Bronze. |
| Lambda-to-Lambda invocation | Silver invokes Gold after successful completion. |

This enables the flow to advance from ingestion to Gold tables without manual intervention.

---

## 13. IAM and Permissions

The required permissions include:

- `tmdb_to_bronze` Lambda with access to Secrets Manager and write permissions on S3 Bronze.
- `bronce_tmdb_to_silver` Lambda with read permissions on Bronze and write permissions on Silver.
- `silver_tmdb_to_gold` Lambda with permissions to run Athena, query Glue, create/drop tables, and clean S3 Gold paths.
- Athena with permissions over S3 for reading Silver, writing results, and creating Gold tables.
- Glue with permissions to register metadata.

All permissions must follow the principle of least privilege.

---

## 14. Monitoring and Validation

Technical validation is performed through:

- Lambda logs in CloudWatch.
- Files generated in S3 Bronze.
- Parquet files generated in S3 Silver.
- Gold tables generated in S3 and Athena.
- Successful Glue Crawler execution.
- Successful Athena queries.
- Connected dashboard in Power BI.

Implementation evidence will be stored in the `img/` directory of the repository. This folder will include the architecture diagram, sequence and/or flow diagrams, and screenshots proving that the solution was implemented in AWS.

---

## 15. Common Errors and Actions

| Error | Probable Cause | Action |
|---|---|---|
| Lambda does not query TMDb | Invalid API Key or misconfigured secret | Review Secrets Manager and logs. |
| No file appears in Bronze | Permission error or incorrect S3 path | Review IAM and bucket. |
| Silver does not run | Misconfigured S3 Event Notification | Validate the S3 event. |
| Gold is not generated | Lambda invocation error or Athena permissions issue | Review Lambda-Athena-Glue-S3 permissions. |
| CTAS error | S3 Gold path already exists | Clean the Gold folder before recreating the table. |
| Athena does not show new columns | Crawler not updated | Rerun the crawler. |
| Power BI does not connect | Incorrect DSN, region, or credentials | Review ODBC and Athena configuration. |

---

## 16. Cost and Scope Decisions

Glue Jobs, EMR, Redshift, RDS, and QuickSight were not used as production components because the data volume is low and the system objective can be solved with serverless and on-demand services.

Lambda, EventBridge, S3, Glue Data Catalog, and Athena keep the architecture simple, cost-efficient, and defensible. Power BI was chosen as the visualization tool because it enables an executive dashboard without adding permanent infrastructure inside AWS.

---

## 17. Conclusion

The technical solution implements an end-to-end serverless pipeline to support catalog management for a streaming platform. The system ingests TMDb data, transforms it into Bronze, Silver, and Gold layers, generates analytical tables through Athena, and allows results to be consumed in Power BI for executive analysis.
