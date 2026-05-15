# aws-movie-data-pipeline
A serverless data engineering pipeline built on AWS to analyze movie popularity. It implements a Medallion architecture (Bronze, Silver, Gold layers) using Amazon S3 and AWS Lambda for automated ETL processes.

# 🎬 AWS Serverless Data Pipeline: TMDb Movie Analytics

![AWS](https://img.shields.io/badge/AWS-%23FF9900.svg?style=for-the-badge&logo=amazon-aws&logoColor=white)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Apache Parquet](https://img.shields.io/badge/Apache%20Parquet-white?style=for-the-badge&logo=apache&logoColor=blue)

## 📌 Business Case & Overview
[cite_start]This project was developed for a streaming company that needs to evaluate the recent market of popular movies to make data-driven decisions about its catalog[cite: 4]. [cite_start]The company seeks to identify which genres and movies to include, prioritize, recommend, or avoid promoting, using external TMDb data such as popularity, average rating, and vote volume[cite: 5].

[cite_start]The solution establishes a fully serverless, event-driven data pipeline on AWS utilizing a Medallion Architecture (Bronze, Silver, and Gold layers)[cite: 6]. [cite_start]The final Gold layer transforms cleaned data into analytical tables to directly support business decisions regarding audiovisual content[cite: 7].

## 🏗️ Architecture & Data Flow

![Architecture Diagram](Link_to_your_architecture_diagram.png)
*(Note: Replace the link above with the URL of your architecture image)*

[cite_start]The pipeline runs on a lightweight, event-driven architecture designed for cost-efficiency without relying on always-on clusters[cite: 11, 74]. [cite_start]The flow is fully automated up to the Gold layer: EventBridge initiates the ingestion, S3 triggers the Silver processing, and Silver invokes Gold upon successful completion[cite: 12].

1. [cite_start]**Ingestion:** Amazon EventBridge Scheduler triggers the `tmdb_to_bronze` Lambda function[cite: 15, 17].
2. [cite_start]**Raw Storage:** Data is fetched from the TMDb API and stored in S3 `1bronce/tmdb/popular/`[cite: 13, 19].
3. [cite_start]**Event Notification:** An S3 Event Notification automatically triggers the `bronce_tmdb_to_silver` Lambda[cite: 20, 21].
4. [cite_start]**Refined Storage:** The data is cleaned and saved in S3 `2silver/movies/`[cite: 23].
5. [cite_start]**Analytics Generation:** The Silver Lambda automatically invokes the `silver_tmdb_to_gold` Lambda[cite: 24, 25].
6. [cite_start]**Business Tables:** Amazon Athena uses CTAS queries to generate the final analytical tables in S3 `3gold/`[cite: 27, 29].

## 🛠️ Tech Stack & AWS Services
* **Language:** Python 3.x (`boto3`, `requests`, `pandas`, `pyarrow`)
* [cite_start]**Amazon S3:** Main Data Lake storing Bronze, Silver, and Gold layers[cite: 36].
* [cite_start]**AWS Lambda:** Executes ingestion, Silver transformation, and Gold generation[cite: 36].
* [cite_start]**Amazon EventBridge Scheduler:** Schedules ingestion for Mondays and Fridays at 8:00 a.m.[cite: 36].
* [cite_start]**AWS Glue Data Catalog & Crawler:** Metadata catalog to query S3 files as tables and detect schema/partitions in Silver[cite: 36].
* [cite_start]**Amazon Athena:** SQL engine used to validate data and create Gold tables via CTAS[cite: 36].
* [cite_start]**AWS Secrets Manager:** Securely stores the TMDb API Key and sensitive configurations[cite: 36].
* [cite_start]**IAM Roles:** Manages strict permissions across Lambda, S3, Athena, and Glue[cite: 36].

## 📊 Data Layers (Medallion Architecture)

| Layer | S3 Path | Description |
| :--- | :--- | :--- |
| **Bronze** | `1bronce/tmdb/popular/` | [cite_start]Raw snapshot data from TMDb by ingestion date[cite: 48]. |
| **Silver** | `2silver/movies/` | [cite_start]Cleaned, filtered, and deduplicated historical data stored in Parquet format[cite: 48]. |
| **Gold** | `3gold/` | [cite_start]Final analytical tables ready to answer business questions[cite: 48]. |

## 💡 Business Value (Gold Tables)
[cite_start]The Gold layer translates raw data into actionable insights for the streaming business[cite: 8]:

* [cite_start]**`gold_performance_genero`**: Identifies attractive genres to strengthen the catalog[cite: 9].
* [cite_start]**`gold_ranking_peliculas`**: Prioritizes titles with a good mix of popularity, rating, and votes[cite: 9].
* [cite_start]**`gold_peliculas_sobreexpuestas`**: Detects highly popular content with low ratings that might disappoint users[cite: 9].
* [cite_start]**`gold_tendencia_generos`**: Detects recent trends for acquisition and promotional strategies[cite: 9].

## ⚙️ Business & Transformation Rules
* [cite_start]Only movies with a `vote_count >= 100` are considered to avoid unrepresentative ratings[cite: 50].
* [cite_start]The Gold layer utilizes data strictly within a 30-day rolling window[cite: 51].
* [cite_start]To prevent historical duplication, Gold selects the most recent record per movie based on the `ingestion_timestamp`[cite: 52].
* [cite_start]Genres are separated using `UNNEST(split(...))` since a movie can belong to multiple categories[cite: 53].

## 👤 Authors
**Marcos Gabriel Flores Chávez**
**Daniel Adrian Galindo Reyes**
**Julian Bolaños Guerrero**
**Javier Issac Lemus Gónzales**
**Roberto Aburto López**
* [LinkedIn](Insert_your_LinkedIn_URL)
* [GitHub](Insert_your_GitHub_URL)
