# AWS-TMDb-Medallion-Analytics

Automated movie market analytics pipeline using a Medallion Architecture on AWS.

![AWS](https://img.shields.io/badge/AWS-%23FF9900.svg?style=for-the-badge&logo=amazon-aws&logoColor=white)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Apache Parquet](https://img.shields.io/badge/Apache%20Parquet-white?style=for-the-badge&logo=apache&logoColor=blue)

---

# 🎬 AWS Serverless Data Pipeline: TMDb Movie Analytics

## 📋 Table of Contents

- [1. Project Description](#1-project-description)
- [2. Business Purpose & Use Case](#2-business-purpose--use-case)
- [3. Technology Stack](#3-technology-stack)
- [4. Data Architecture](#4-data-architecture)
- [5. Data Flow](#5-data-flow)
- [6. Business Value (Gold Tables)](#6-business-value-gold-tables)
- [7. Transformation & Business Rules](#7-transformation--business-rules)
- [8. Design Decisions & Trade-offs](#8-design-decisions--trade-offs)
- [9. Sample Results](#9-sample-results)
- [10. Future Improvements](#10-future-improvements)
- [11. Repository Structure](#11-repository-structure)
- [12. Deployment](#12-deployment)

---

## 1. Project Description

This project implements an end-to-end **Data Engineering** solution on **Amazon Web Services (AWS)** for a streaming company. The goal is to automate the ingestion, transformation, and analysis of popular movie data from the **TMDb (The Movie Database)** API.

The solution leverages a **Medallion Architecture** (Bronze, Silver, Gold) to ensure data traceability, scalability, and quality, enabling stakeholders to make strategic decisions regarding content acquisition and promotion based on popularity and rating metrics.

---

## 2. Business Purpose & Use Case

The system is designed to answer critical business questions such as:

- **Genre Performance:** Which movie categories are dominating the recent market?

- **Recommendations:** Which titles have the best balance between popularity and audience/critic consensus?

- **Overexposure Detection:** Identify highly popular movies with poor ratings to avoid oversaturating the catalog with low-quality content.

---

## 3. Technology Stack

### Programming Languages
- **Python** (AWS Lambda Functions)

### AWS Infrastructure & Services
- **Amazon S3:** Data Lake storage for Bronze, Silver, and Gold layers.
- **AWS Lambda:** Serverless ingestion and transformation orchestration.
- **Amazon EventBridge:** Cron-based scheduling (Mondays and Fridays at 8:00 AM).
- **AWS Glue (Data Catalog & Crawler):** Schema management and metadata cataloging.
- **Amazon Athena:** SQL query engine and analytical table generation via CTAS.
- **AWS Secrets Manager:** Secure storage for TMDb API credentials.

### Additional Technologies
- **Apache Parquet:** Optimized columnar storage format for the Silver layer.
- **SQL (Trino/Presto Dialect):** Complex transformations and genre `UNNEST` operations.
- **NDJSON:** Raw ingestion file format.

---

## 4. Data Architecture

The pipeline is fully **event-driven**, minimizing idle infrastructure time and optimizing operational costs.

### Bronze Layer
Raw NDJSON data captured directly from the TMDb API.

### Silver Layer
Cleaned and deduplicated datasets with corrected data types and relevance filtering (`vote_count >= 100`).

### Gold Layer
Optimized analytical tables using a rolling 30-day window for current trend analysis.

## Architecture in AWS
<img width="2964" height="1524" alt="WhatsApp Image 2026-05-14 at 5 56 53 p  m" src="https://github.com/user-attachments/assets/72bc2c96-cd94-400a-87fb-f413f3147c1b" />

### Trigger Mechanisms

The pipeline chains three Lambda functions using two distinct trigger patterns, chosen deliberately for each transition:

| Transition | Trigger Type | Rationale |
|---|---|---|
| EventBridge → `tmdb_to_bronze` | Scheduled (cron) | Predictable bi-weekly refresh aligned with reporting cycles |
| Bronze → `bronze_to_silver` | S3 Event Notification | Decoupled and reactive — runs only when new data lands |
| Silver → `silver_to_gold` | Direct Lambda invocation | Guarantees atomic execution and simplifies error propagation |

---

## 5. Data Flow

1. **Ingestion**
   Amazon EventBridge Scheduler triggers the `tmdb_to_bronze` Lambda function.

2. **Bronze Storage**
   Raw data is fetched from the TMDb API and stored in Amazon S3 as NDJSON files.

3. **Event Notification**
   An S3 Event Notification automatically invokes the `bronze_to_silver` Lambda.

4. **Silver Processing**
   Data is cleaned, normalized, filtered, and stored in Parquet format.

5. **Gold Processing**
   The Silver Lambda invokes the `silver_to_gold` Lambda function.

6. **Analytics Generation**
   Amazon Athena generates business-ready analytical tables using CTAS queries.

### Visual Flow

```
┌──────────────────┐
│  EventBridge     │  Cron: Mon & Fri at 08:00 AM
│  (Scheduler)     │
└────────┬─────────┘
         │ invoke
         ▼
┌──────────────────┐      ┌────────────────────┐
│  Lambda:         │◄─────┤  Secrets Manager   │
│  tmdb_to_bronze  │      │  (TMDb API Key)    │
└────────┬─────────┘      └────────────────────┘
         │ fetch popular movies
         ▼
   ┌──────────┐
   │ TMDb API │
   └────┬─────┘
        │ raw JSON
        ▼
┌──────────────────┐
│  S3: Bronze      │  Immutable NDJSON
└────────┬─────────┘
         │ S3 Event Notification
         ▼
┌──────────────────┐
│  Lambda:         │  Clean · Deduplicate · Filter · Cast
│  bronze_to_silver│
└────────┬─────────┘
         │ write Parquet
         ▼
┌──────────────────┐
│  S3: Silver      │  Curated, query-ready Parquet
└────────┬─────────┘
         │ direct Lambda invocation
         ▼
┌──────────────────┐
│  Lambda:         │  Execute CTAS queries on Athena
│  silver_to_gold  │
└────────┬─────────┘
         │ CREATE TABLE AS SELECT
         ▼
┌──────────────────┐      ┌────────────────────┐
│  S3: Gold        │◄────►│  Amazon Athena     │
│  (CTAS Tables)   │      │  (BI / Analysts)   │
└──────────────────┘      └────────────────────┘
```

---

## 6. Business Value (Gold Tables)

The Gold layer transforms raw datasets into actionable insights for the streaming business.

| Table | Business Purpose |
|---|---|
| `gold_genre_performance` | Identifies the most attractive genres for catalog expansion |
| `gold_movie_ranking` | Prioritizes movies with strong popularity and ratings |
| `gold_overexposed_movies` | Detects highly promoted but poorly rated content |
| `gold_genre_trends` | Identifies recent genre trends for acquisition strategies |

---

## 7. Transformation & Business Rules

- Only movies with `vote_count >= 100` are considered to avoid unreliable ratings.
- The Gold layer operates on a strict rolling 30-day analytical window.
- Historical duplication is prevented by selecting the latest record using `ingestion_timestamp`.
- Genres are normalized using `UNNEST(split(...))` because a movie may belong to multiple categories.

---

## 8. Design Decisions & Trade-offs

Honest documentation of architectural choices and their compromises:

### S3 Event vs. Direct Invocation (mixed pattern)
- **Bronze → Silver uses S3 Events:** Loosely coupled, scales naturally with file count, survives Lambda redeployments.
- **Silver → Gold uses Direct Invocation:** Avoids race conditions when multiple Silver files land simultaneously and guarantees a single Athena CTAS execution per pipeline run.

### Athena CTAS vs. AWS Glue ETL
- **Chosen:** Athena CTAS — pay-per-query, zero infrastructure, SQL-native.
- **Trade-off:** Less suitable for ML feature engineering or complex Python transforms. For this analytical workload, SQL is sufficient and dramatically cheaper.

### Lambda vs. AWS Glue / EMR
- **Chosen:** Lambda — sub-second cold starts, no cluster management, free tier covers typical execution volume.
- **Trade-off:** 15-minute execution ceiling and memory limits cap dataset size. For TMDb's popular-movies endpoint (~1–2 MB per run) this is a non-issue. Would not scale to multi-GB datasets without re-architecting.

### Bi-weekly cron vs. real-time streaming
- **Chosen:** Bi-weekly cron — TMDb popularity scores update slowly; streaming offers no business value.
- **Trade-off:** Not suitable for time-sensitive use cases (e.g., release-day tracking).

### `vote_count >= 100` threshold
- **Chosen:** Hard filter at Silver layer.
- **Trade-off:** Niche or newly-released films are excluded. Acceptable because the business questions target mainstream catalog strategy, not long-tail discovery.


---

## 9. Sample Results

Example expected output for `gold_genre_performance`:

| genre | movie_count | avg_popularity | avg_rating |
|---|---|---|---|
| Action | 42 | 1247.85 | 7.21 |
| Drama | 38 | 982.43 | 7.68 |
| Comedy | 31 | 856.12 | 6.94 |
| Thriller | 27 | 1103.67 | 7.05 |
| Science Fiction | 24 | 1389.21 | 7.42 |

---

## 10. Future Improvements

Although the project is functional and cost-efficient for medium-scale workloads, several improvement areas were identified:

- **Infrastructure as Code (IaC):**
  Migrate infrastructure provisioning to Terraform or AWS CloudFormation for repeatable deployments.

- **Data Quality Validation:**
  Integrate AWS Glue Data Quality or libraries such as Great Expectations within the Silver layer.

- **Data Visualization:**
  Connect Gold layer tables to dashboards using Amazon QuickSight or Power BI.

- **Monitoring & Alerts:**
  Configure Amazon CloudWatch Alarms and SNS notifications for Lambda failures.

- **CI/CD Pipeline:**
  Implement GitHub Actions workflows for automated Lambda deployment and validation.

---

## 11. Repository Structure

```bash
.
├── lambda/
│   ├── tmdb_to_bronze/
│   ├── bronze_to_silver/
│   └── silver_to_gold/
├── queries/
│   └── athena/
├── architecture/
├── docs/
└── README.md
```

---

## 12. Deployment

### Prerequisites

- AWS account with permissions for Lambda, S3, EventBridge, Glue, Athena, and Secrets Manager
- TMDb API key ([get one here](https://www.themoviedb.org/settings/api))
- Python 3.11
- AWS CLI configured locally

### Setup Steps

1. **Store the TMDb API key** in AWS Secrets Manager under a secret named `tmdb/api-key`.
2. **Create S3 buckets** for each layer: `tmdb-bronze`, `tmdb-silver`, `tmdb-gold`.
3. **Deploy the three Lambda functions** with the code under `lambda/`.
4. **Configure the EventBridge rule** with cron expression `cron(0 8 ? * MON,FRI *)`.
5. **Enable S3 Event Notifications** on the Bronze bucket targeting `bronze_to_silver`.
6. **Run the Glue Crawler** to populate the Data Catalog with the Silver schema.
7. **Configure Athena** query results location in S3.
