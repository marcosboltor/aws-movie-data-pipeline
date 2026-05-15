# AWS-TMDb-Medallion-Analytics

Automated movie market analytics pipeline using a Medallion Architecture on AWS.

![AWS](https://img.shields.io/badge/AWS-%23FF9900.svg?style=for-the-badge&logo=amazon-aws&logoColor=white)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Apache Parquet](https://img.shields.io/badge/Apache%20Parquet-white?style=for-the-badge&logo=apache&logoColor=blue)

---

# 🎬 AWS Serverless Data Pipeline: TMDb Movie Analytics

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

## 8. Future Improvements

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

## 9. Repository Structure

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
