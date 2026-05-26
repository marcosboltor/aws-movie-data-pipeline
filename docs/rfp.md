# Request for Proposal (RFP)  
# Streaming Platform - Data Infrastructure for Catalog Management

**Client:** Streaming Platform  
**Project:** Audiovisual catalog analytics with TMDb and AWS  
**Date:** May 2026

---

## 1. Introduction and Background

A streaming platform needs to strengthen its catalog decision-making process. Currently, movie selection, promotion, and prioritization need to be supported by recent market data in order to identify which titles and genres show stronger performance.

The company seeks to analyze external information from TMDb to understand popularity, average rating, vote volume, genres, and recent movie trends. This information will complement editorial and commercial catalog criteria with analytical evidence.

To address this need, a data solution on AWS is requested to automate the ingestion, transformation, querying, and visualization of information relevant to catalog management.

---

## 2. RFP Objective

The objective of this request is to select a technical proposal to implement a data architecture on AWS that allows the streaming platform to analyze popular movies and generate indicators useful for catalog decisions.

The solution must support, through analytical tables and executive visualizations, questions such as:

- Which genres have the best recent performance?
- Which movies should be recommended or promoted?
- Which movies are popular but have low ratings?
- Which genres are growing in popularity?

---

## 3. Required Technical Scope

The proposal must cover the following components.

### 3.1 Data Source

The solution must consume information from the TMDb API, specifically from the popular movies endpoint. The API Key must be managed securely and must not be exposed in the source code.

### 3.2 Data Architecture

A Medallion architecture is required with the following layers:

| Layer | Purpose |
|---|---|
| Bronze | Store raw TMDb data by ingestion date. |
| Silver | Generate clean, filtered, structured data in Parquet format. |
| Gold | Create analytical tables aligned with catalog-related business questions. |

### 3.3 Pipeline Automation

The flow must be automated end to end:

1. EventBridge schedules the ingestion.
2. Lambda queries TMDb and stores data in Bronze.
3. S3 Event Notification triggers the Silver transformation.
4. Silver automatically invokes Gold generation.
5. Athena creates or updates Gold tables using CTAS.
6. Power BI consumes Gold from Athena.

### 3.4 Analytical Querying

Amazon Athena must be used as the SQL engine to query data stored in S3. AWS Glue Data Catalog must register the required metadata so tables can be queried.

### 3.5 Visualization

Power BI Desktop must connect to Athena through ODBC to build an executive dashboard with catalog indicators. For a production scenario, the proposal must consider the possibility of publishing the report to Power BI Service and refreshing it through Power BI Gateway.

### 3.6 Security

The proposal must consider:

- Secret management with AWS Secrets Manager.
- IAM roles with the minimum required permissions.
- Protection of S3 paths.
- No credential exposure in GitHub.
- Logical separation of data layers.

---

## 4. Proposal Requirements

| Section | Expected Content |
|---|---|
| Team Profile | Experience in AWS, Python, SQL, data modeling, and visualization. |
| Methodology | Design, implementation, validation, and delivery phases. |
| Architecture | Proposed AWS services and complete data flow. |
| Ingestion | Strategy to consume TMDb API and store raw snapshots. |
| Transformation | Rules for cleaning, filtering, and structuring data. |
| Gold Layer | Analytical tables oriented to catalog decisions. |
| Visualization | Athena-Power BI connection and executive dashboard proposal. |
| Security | Secret management, IAM permissions, and repository protection. |
| Costs | Justification of serverless and on-demand services. |
| Deliverables | Code, documentation, diagrams, evidence, and presentation. |

---

## 5. Minimum Business Rules

The solution must consider the following rules:

- Only movies with `vote_count >= 100` are considered to avoid non-representative ratings.
- The Gold layer works with a 30-day rolling window.
- If a movie appears multiple times across historical runs, Gold uses the most recent record.
- A movie may belong to multiple genres; genre analysis must account for this relationship.
- Performance must combine popularity, rating, and vote volume.
- Power BI only consumes processed data; it does not modify the Data Lake.

---

## 6. Expected Gold Tables

| Gold Table | Business Question | Expected Use |
|---|---|---|
| `gold_performance_genero` | Which genres have the best recent performance? | Identify attractive genres to strengthen the catalog. |
| `gold_ranking_peliculas` | Which movies should be recommended or promoted? | Prioritize titles with a strong mix of popularity, rating, and votes. |
| `gold_peliculas_sobreexpuestas` | Which movies are popular but have low ratings? | Detect content that may not meet user expectations. |
| `gold_tendencia_generos` | Which genres are growing in popularity? | Identify recent trends for acquisition and promotion. |

---

## 7. Evaluation Criteria

Proposals will be evaluated according to:

| Criterion | Weight |
|---|---|
| Understanding of the streaming business case | 25% |
| Soundness of the AWS architecture | 25% |
| Pipeline automation and traceability | 20% |
| Usefulness of Gold tables and executive visualization | 15% |
| Security and cost management | 10% |
| Documentation clarity and ease of replication | 5% |

---

## 8. Expected Deliverables

- Structured GitHub repository.
- Lambda source code.
- Athena SQL queries for Gold.
- Infrastructure template or infrastructure documentation.
- Functional documentation.
- Technical documentation.
- Architecture documentation.
- SOW.
- RFP.
- Architecture and flow diagrams.
- AWS implementation screenshots.
- Evidence of Power BI-Athena connection.
- Executive presentation.

---

## 9. Constraints

- The solution must avoid unnecessary permanent services.
- Credentials and API Keys must not be exposed.
- Redshift, RDS, EMR, Glue Jobs, or QuickSight are not required as part of the production pipeline.
- The solution must be suitable for a low to moderate data volume.
- The design must favor serverless and on-demand services.

---

## 10. Conclusion

The requested solution must allow a streaming platform to transform external TMDb data into actionable information for catalog management. The focus is not only on storing data, but on generating analytical tables and visualizations that support decisions about genres, movies, promotion, and market trends.
