# Statement of Work (SOW)  
# Streaming Platform - Catalog Analytics with TMDb and AWS

**Client:** Streaming Platform  
**Project:** AWS Data Lake for data-driven audiovisual catalog management  
**Date:** May 2026  
**Team:**  
Galindo Reyes Daniel Adrian  
Lemus González Javier Issac  
Roberto Aburto López  
Flores Chávez Marcos Gabriel  
Bolaños Guerrero Julian

---

## 1. Project Summary

This project consists of designing and implementing a data analytics solution for a streaming platform that needs to make more informed decisions regarding its movie catalog.

The company needs to evaluate the recent market behavior of popular movies in order to identify which genres and titles should be acquired, prioritized, recommended, promoted, or handled with caution. For this purpose, the solution uses external data from TMDb, including popularity, average rating, vote volume, genres, release date, and original language.

The implemented solution uses an AWS data pipeline based on a Bronze, Silver, and Gold architecture. The Gold layer generates business-oriented analytical tables, and Power BI presents the results through an executive dashboard connected to Athena via ODBC.

---

## 2. General Objective

Implement a data architecture on AWS that enables a streaming platform to analyze recent information about popular movies and support decisions related to content acquisition, recommendation, and promotion.

---

## 3. Specific Objectives

- Ingest popular movie data from the TMDb API.
- Store raw snapshots in Amazon S3 within the Bronze layer.
- Transform the data into a clean, filtered, typed Silver layer in Parquet format.
- Generate Gold analytical tables focused on catalog-related business questions.
- Automate the ingestion and transformation flow using EventBridge, S3 Event Notification, and AWS Lambda.
- Query the analytical tables using Amazon Athena.
- Visualize results in Power BI Desktop connected to Athena through ODBC.
- Maintain a serverless, cost-efficient design suitable for the project’s data volume.

---

## 4. Scope of Work

The scope includes the following activities.

### 4.1 Data Ingestion

- Configuration of a Lambda function named `tmdb_to_bronze`.
- Querying the TMDb `/movie/popular` endpoint.
- Extracting pages 1 to 5 per execution, equivalent to approximately 100 movies per run.
- Adding metadata such as `source_page`, `ingestion_timestamp`, and `ingestion_date`.
- Storing raw data in S3 Bronze in NDJSON format.

### 4.2 Bronze Layer

- Preservation of raw data obtained from TMDb.
- File organization under the following path:

```text
1bronce/tmdb/popular/
```

- Use of Bronze as a traceability and reprocessing source.

### 4.3 Silver Layer

- Automatic activation through S3 Event Notification when new files arrive in Bronze.
- Execution of the `bronce_tmdb_to_silver` Lambda function.
- Data cleaning and normalization.
- Genre mapping.
- Date conversion.
- Filtering movies with `vote_count >= 100`.
- Removal of duplicates within the batch.
- Writing clean data in Parquet format under:

```text
2silver/movies/
```

### 4.4 Gold Layer

- Automatic invocation of the `silver_tmdb_to_gold` Lambda function once Silver finishes successfully.
- Cleaning of Gold folders before recreating tables.
- Creation of analytical tables using Athena CTAS.
- Use of a 30-day rolling window.
- Selection of the most recent record per movie using `ingestion_timestamp`.
- Splitting genres with `UNNEST(split(...))` when a movie belongs to multiple genres.

The Gold tables considered are:

```text
gold_performance_genero
gold_ranking_peliculas
gold_peliculas_sobreexpuestas
gold_tendencia_generos
```

### 4.5 Query and Visualization

- Use of Athena as the SQL engine over S3.
- Use of Glue Data Catalog to register metadata.
- Connection of Power BI Desktop to Athena through generic ODBC using the Amazon Athena driver.
- Development of an executive dashboard to visualize catalog indicators.

---

## 5. Out of Scope

The following elements are not part of the production scope of this solution:

- Use of Glue Jobs, EMR, Redshift, RDS, or QuickSight as main components.
- Implementation of a user-level personalized recommendation system.
- Training of machine learning models.
- Advanced data governance with Lake Formation.
- Multi-environment production deployment.
- Enterprise high availability.
- Full infrastructure automation through CI/CD, except for a base template or documentation.

These exclusions were defined because the data volume is low and the business case can be efficiently solved with serverless and on-demand services.

---

## 6. Deliverables

| Deliverable | Description |
|---|---|
| GitHub Repository | Organized project with documentation, code, diagrams, evidence, and tests. |
| Lambda Code | Lambda functions for Bronze ingestion, Silver transformation, and Gold generation. |
| Athena SQL Scripts | CTAS queries and validation queries over Gold tables. |
| Functional Documentation | Explanation of the system from the business perspective of a streaming platform. |
| Technical Documentation | Details of services, paths, Lambda functions, tables, permissions, execution, and monitoring. |
| Architecture Documentation | Description of the end-to-end flow, Medallion architecture, and visualization layer. |
| RFP | Request for Proposal focused on the need for catalog analytics. |
| SOW | Formal scope of the work performed. |
| Diagrams | Architecture diagram and pipeline flow diagram. |
| Evidence | AWS and Power BI screenshots proving the implementation. |
| Executive Presentation | Presentation explaining business value, architecture, and results. |
| Tests | Unit, integration, or configuration tests, if performed. |

---

## 7. Estimated Timeline

| Phase | Activities |
|---|---|
| Phase 1 | Definition of the business case and catalog analytics questions. |
| Phase 2 | Design of the Bronze, Silver, and Gold architecture on AWS. |
| Phase 3 | Implementation of TMDb ingestion into S3 Bronze. |
| Phase 4 | Development of the Silver transformation with cleaning, filtering, and Parquet output. |
| Phase 5 | Generation of Gold tables with Athena CTAS. |
| Phase 6 | Automation with EventBridge, S3 Event Notification, and Lambda-to-Lambda invocation. |
| Phase 7 | Connection between Power BI and Athena and construction of the executive dashboard. |
| Phase 8 | Documentation, evidence, tests, and repository preparation. |

---

## 8. Acceptance Criteria

The project will be considered accepted if it meets the following criteria:

- The `tmdb_to_bronze` Lambda function correctly queries TMDb and stores data in Bronze.
- Ingestion runs on a schedule through EventBridge.
- The arrival of data in Bronze automatically triggers the Silver process.
- Silver generates clean Parquet files in `2silver/movies/`.
- Silver filters records with `vote_count >= 100` and preserves fields relevant for analysis.
- Gold is generated automatically after Silver finishes.
- Gold tables are created through Athena CTAS.
- Gold tables answer business questions about genre performance, movie rankings, overexposed movies, and trends.
- Athena can query the project tables.
- Power BI Desktop can consume Gold tables from Athena through ODBC.
- The repository does not expose API keys, secrets, or credentials.
- The documentation makes it possible to understand, review, and replicate the general system flow.

---

## 9. Assumptions

- The TMDb API is available during executions.
- The TMDb API Key is securely managed in AWS Secrets Manager.
- The data volume remains within a range compatible with Lambda, S3, and Athena.
- The streaming platform uses this data as market analysis support, not as the only source of decision-making.
- Power BI Desktop supports manual dashboard refresh.
- For production refresh, the dashboard could be published to Power BI Service and updated through Power BI Gateway.

---

## 10. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| API Key exposure | Use Secrets Manager and exclude secrets from the repository. |
| Low-representativeness data | Filter movies with `vote_count >= 100`. |
| Duplicates from multiple ingestions | Select the most recent record per movie in Gold. |
| Unnecessary costs | Schedule ingestion only on Mondays and Fridays and use on-demand services. |
| Changes in TMDb structure | Validate the schema in Silver and update transformations when necessary. |
| Errors recreating Gold tables | Clean S3 Gold folders before executing CTAS. |
| Power BI-Athena connection failures | Document ODBC configuration, DSN, and Athena result location. |

---

## 11. Conclusion

This SOW defines the scope of an analytics solution for a streaming platform that needs to manage its catalog using external market data. The architecture automates ingestion, cleaning, refinement, querying, and visualization of popular movie data using AWS and Power BI.
