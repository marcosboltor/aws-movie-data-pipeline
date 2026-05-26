# Architecture Documentation  
# AWS/TMDb Data Lake for Streaming Catalog Management

**Client:** Streaming Platform  
**Project:** Audiovisual catalog analytics with TMDb and AWS  
**Date:** May 2026  
**Version:** 2.0

---

## 1. Executive Summary

This document describes the data architecture implemented for a streaming platform that needs to analyze recent information about popular movies and use it as support for catalog decisions.

The solution uses a Medallion architecture with Bronze, Silver, and Gold layers on Amazon S3. The flow is automated end to end through EventBridge, S3 Event Notification, and AWS Lambda. Amazon Athena creates and queries Gold analytical tables, and Power BI consumes these results to present an executive dashboard.

---

## 2. Architecture Objective

The architecture aims to transform external TMDb data into actionable information for catalog decisions, including:

- Identification of genres with the best recent performance.
- Prioritization of recommendable or promotable movies.
- Detection of popular movies with low ratings.
- Identification of genres with recent growth.
- Executive visualization of indicators in Power BI.

---

## 3. Conceptual Diagram

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

## 4. Technology Stack

| Component | Service / Tool | Function |
|---|---|---|
| External source | TMDb API | Provides popular movie data. |
| Initial orchestration | EventBridge Scheduler | Schedules ingestion on Mondays and Fridays at 8:00 a.m. |
| Ingestion | AWS Lambda | Queries TMDb and stores data in Bronze. |
| Storage | Amazon S3 | Stores Bronze, Silver, and Gold layers. |
| Intermediate automation | S3 Event Notification | Triggers Silver when new files are detected in Bronze. |
| Transformation | AWS Lambda | Cleans data and generates Silver. |
| Analytical generation | AWS Lambda + Athena CTAS | Recreates business-oriented Gold tables. |
| Catalog | AWS Glue Data Catalog | Registers metadata queryable by Athena. |
| Schema discovery | AWS Glue Crawler | Detects Silver schema and partitions. |
| Query | Amazon Athena | Queries Silver/Gold and generates CTAS tables. |
| Visualization | Power BI Desktop | Executive dashboard connected to Athena through ODBC. |
| Security | IAM + Secrets Manager | Permission and secret management. |
| Development | Amazon EC2 | Testing environment; not part of the production pipeline. |

---

## 5. Medallion Architecture

### 5.1 Bronze

The Bronze layer preserves raw data obtained from TMDb. Its main value is traceability: it keeps snapshots of each ingestion and allows data to be reprocessed if necessary.

Path:

```text
1bronce/tmdb/popular/
```

Characteristics:

- NDJSON format.
- Data by ingestion date.
- Approximately 100 movies per execution.
- Includes `source_page`, `ingestion_timestamp`, and `ingestion_date`.

---

### 5.2 Silver

The Silver layer contains clean, filtered data ready for structured querying.

Path:

```text
2silver/movies/
```

Characteristics:

- Parquet format.
- Clean historical data.
- `vote_count >= 100` filter.
- Genre mapping.
- Date and numeric type conversion.
- Removal of duplicates within the batch.
- Recognition through Glue Crawler and Glue Data Catalog.

---

### 5.3 Gold

The Gold layer contains analytical tables oriented to the streaming business.

Path:

```text
3gold/
```

Tables:

| Table | Use |
|---|---|
| `gold_performance_genero` | Identify genres with the best recent performance. |
| `gold_ranking_peliculas` | Prioritize movies for recommendation or promotion. |
| `gold_peliculas_sobreexpuestas` | Detect popular movies with low ratings. |
| `gold_tendencia_generos` | Identify genres with recent growth. |

Characteristics:

- Created through Athena CTAS.
- 30-day rolling window.
- Most recent record per movie.
- Automatic cleanup of S3 Gold folders before recreating tables.
- Splitting of multiple genres with `UNNEST(split(...))`.

---

## 6. Data Flow

1. EventBridge runs `tmdb_to_bronze` on Mondays and Fridays at 8:00 a.m.
2. The Lambda function queries TMDb `/movie/popular`, pages 1 to 5.
3. Data is stored in Bronze in NDJSON format.
4. S3 Event Notification detects the new file and triggers `bronce_tmdb_to_silver`.
5. Silver cleans, filters, maps genres, and writes Parquet files to `2silver/movies/`.
6. Once Silver finishes successfully, it invokes `silver_tmdb_to_gold`.
7. Gold drops previous tables and cleans S3 Gold paths.
8. Athena CTAS recreates the four analytical tables.
9. Athena exposes Gold tables for querying.
10. Power BI Desktop consumes the tables through ODBC.
11. The dashboard presents executive catalog results.

---

## 7. Visualization Layer

The visualization layer is implemented with Power BI Desktop connected to Athena through ODBC.

Data source:

```text
db_movies_tmdb.gold_performance_genero
db_movies_tmdb.gold_ranking_peliculas
db_movies_tmdb.gold_peliculas_sobreexpuestas
db_movies_tmdb.gold_tendencia_generos
```

The dashboard analyzes:

- General KPIs.
- Genre performance.
- Genre trends.
- Ranking of recommendable movies.
- Overexposed movies.

In a production scenario, the report can be published to Power BI Service and refreshed through Power BI Gateway after each pipeline execution.

---

## 8. Security

The architecture considers:

- Use of Secrets Manager for the TMDb API Key.
- IAM roles following the principle of least privilege.
- Permission separation by Lambda function.
- Read and write controls by S3 path.
- Specific permissions for Athena, Glue, and S3 Gold.
- No exposure of secrets in GitHub.
- Evidence screenshots without showing keys or credentials.

---

## 9. Architecture Decisions

| Decision | Justification |
|---|---|
| Use S3 as Data Lake | Scalable, cost-efficient, and compatible with Athena. |
| Use Bronze/Silver/Gold architecture | Enables traceability, cleaning, and business analysis. |
| Use Lambda | Avoids permanent servers and reduces costs. |
| Use EventBridge | Allows scheduled and controlled ingestion. |
| Use S3 Event Notification | Automates the Bronze-to-Silver step. |
| Use Athena CTAS for Gold | Generates analytical tables without a dedicated database engine. |
| Use Power BI | Enables executive visualization and business user consumption. |
| Do not use EMR/Redshift/RDS | The data volume does not justify heavier or more expensive services. |

---

## 10. Cost Considerations

The design relies on serverless or on-demand services:

- Lambda charges per execution.
- S3 charges for storage.
- Athena charges based on scanned data.
- EventBridge has a low cost for scheduling.
- Glue Crawler runs only when necessary.
- Power BI is used as an external visualization tool.

The Monday and Friday schedule reduces unnecessary executions while maintaining a reasonable balance between freshness and cost.

---

## 11. Limitations

- TMDb is an external source and does not reflect the platform’s actual internal consumption.
- The analysis does not include licensing costs or legal availability of titles.
- Power BI Desktop requires manual refresh.
- Production refresh requires Power BI Service and Gateway.
- User-level personalization is not implemented.
- The solution is optimized for low or moderate data volumes.

---

## 12. Future Improvements

- Automate infrastructure with CloudFormation.
- Add automatic data quality tests.
- Include additional TMDb endpoints.
- Publish the dashboard in Power BI Service.
- Schedule refresh with Power BI Gateway.
- Add licensing cost metrics if available.
- Combine TMDb data with internal viewing metrics from the platform.
- Implement a recommendation model in a later phase.

---

## 13. Conclusion

The architecture enables a streaming platform to transform external TMDb data into useful indicators for catalog management. The automated Bronze, Silver, and Gold flow provides traceability, cleaning, analysis, and executive visualization without using heavy services or unnecessary permanent infrastructure.
