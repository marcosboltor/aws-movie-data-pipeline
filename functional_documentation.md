# Functional Documentation  
# Catalog Analytics System for a Streaming Platform

**Client:** Streaming Platform  
**Project:** Audiovisual catalog analytics with TMDb and AWS  
**Date:** May 2026  
**Version:** 2.0

---

## 1. Document Objective

This document describes the system from a business perspective. Its purpose is to explain what the solution does, which users interact with it, which decisions it supports, and what value it delivers to a streaming platform.

The system analyzes recent information about popular movies obtained from TMDb to support data-driven catalog management: content acquisition, title prioritization, movie promotion, and genre trend detection.

---

## 2. Functional System Description

The streaming platform needs to evaluate the recent market behavior of popular movies in order to strengthen its catalog with better decision criteria. To achieve this, the system retrieves TMDb data, processes it on AWS, and delivers analytical tables ready for querying and visualization.

The solution is not intended to replace the platform’s editorial or commercial strategy. Its role is to provide quantitative evidence to support decisions about which genres and movies may be more attractive to users.

---

## 3. Business Questions Answered

The Gold layer is designed to answer four main business questions:

| Business Question | Gold Table | Business Use |
|---|---|---|
| Which genres have the best recent performance? | `gold_performance_genero` | Identify attractive genres to strengthen the catalog. |
| Which movies should be recommended or promoted? | `gold_ranking_peliculas` | Prioritize titles with a good mix of popularity, rating, and votes. |
| Which movies are popular but have low ratings? | `gold_peliculas_sobreexpuestas` | Detect overexposed content that may not meet expectations. |
| Which genres are growing in popularity? | `gold_tendencia_generos` | Detect recent trends for acquisition and promotion. |

---

## 4. System Users

| Role | Responsibilities |
|---|---|
| Catalog Analyst | Interprets Gold tables to support acquisition, promotion, and prioritization decisions. |
| Content Team | Uses results to identify genres or movies with catalog potential. |
| Marketing Team | Reviews rankings and trends to define promotional campaigns. |
| Data Engineer | Maintains the ingestion, transformation, and data publishing pipeline. |
| Management / Stakeholder | Reviews the executive dashboard in Power BI for high-level decision-making. |

---

## 5. Supported Business Processes

### 5.1 Genre Performance Evaluation

The system calculates aggregated metrics by genre to identify categories with the best recent performance. This helps decide which types of movies could be strengthened within the catalog.

**Main output:** `gold_performance_genero`.

### 5.2 Prioritization of Recommendable Movies

The system generates a movie ranking based on a combination of popularity, rating, and vote volume. This helps identify titles with positive signals for promotion or catalog inclusion.

**Main output:** `gold_ranking_peliculas`.

### 5.3 Detection of Overexposed Content

The system identifies movies with high popularity but low ratings. This information helps avoid promoting content that may create high expectations but low satisfaction.

**Main output:** `gold_peliculas_sobreexpuestas`.

### 5.4 Identification of Genre Trends

The system analyzes genres with recent popularity growth. This supports acquisition, curation, and campaign decisions around emerging trends.

**Main output:** `gold_tendencia_generos`.

### 5.5 Executive Visualization

Power BI consumes Gold tables from Athena to present KPIs, rankings, and trends in an executive dashboard. This makes the results easier to interpret for non-technical users.

---

## 6. Use Cases

### Use Case 1: Identify Attractive Genres for the Catalog

**Main actor:** Catalog Analyst.  
**Input:** `gold_performance_genero` table.  
**Flow:**

1. The analyst reviews recent performance by genre.
2. Popularity, rating, and vote volume are compared.
3. Genres with positive signals are identified.
4. The analyst proposes strengthening the catalog in those genres.

**Expected result:** List of priority genres for commercial analysis.

---

### Use Case 2: Prioritize Movies for Promotion

**Main actor:** Marketing Team.  
**Input:** `gold_ranking_peliculas` table.  
**Flow:**

1. The team reviews the ranking of recommendable movies.
2. Titles with a strong balance between popularity and rating are selected.
3. Candidate titles are defined for campaigns or highlighted recommendations.

**Expected result:** Selection of movies with stronger promotion potential.

---

### Use Case 3: Avoid Promoting Content with Low Potential Satisfaction

**Main actor:** Content or Marketing Team.  
**Input:** `gold_peliculas_sobreexpuestas` table.  
**Flow:**

1. The user reviews movies with high popularity and low rating.
2. The user evaluates whether promotion should be limited.
3. The catalog visibility strategy is adjusted.

**Expected result:** Identification of titles that may require caution in promotion.

---

### Use Case 4: Detect Recent Trends

**Main actor:** Management or Strategy Team.  
**Input:** `gold_tendencia_generos` table.  
**Flow:**

1. The user reviews genres with recent growth.
2. Trends are compared against the catalog strategy.
3. Opportunities for acquisition or themed campaigns are defined.

**Expected result:** Inputs for strategic catalog decisions.

---

## 7. Business Rules

- Only movies with `vote_count >= 100` are considered.
- The Gold layer analyzes a 30-day rolling window.
- If a movie appears multiple times in the historical data, Gold uses the most recent record based on `ingestion_timestamp`.
- A movie may belong to multiple genres.
- Genre analysis splits multiple genres using `UNNEST(split(...))`.
- The performance score combines popularity, rating, and vote volume.
- Bronze preserves raw snapshots.
- Silver preserves clean historical data.
- Gold represents a recent analytical business view.
- Power BI does not modify the Data Lake; it only consumes processed results.

---

## 8. Inputs and Outputs

### 8.1 Inputs

- Popular movie data from TMDb API.
- Genres, popularity, average rating, vote volume, release date, and language.
- Ingestion metadata such as `source_page`, `ingestion_timestamp`, and `ingestion_date`.

### 8.2 Outputs

- Raw data in Bronze.
- Clean data in Silver.
- Analytical Gold tables.
- Queries available in Athena.
- Executive dashboard in Power BI.

---

## 9. Business Indicators

| Indicator | Use |
|---|---|
| Average popularity by genre | Detect genres with higher market attraction. |
| Average rating by genre | Evaluate perceived quality. |
| Vote volume by genre | Measure rating representativeness. |
| Performance score | Prioritize genres or titles by combining popularity, votes, and rating. |
| Movie ranking | Identify recommendable or promotable titles. |
| Overexposed movies | Detect popular movies with low ratings. |
| Genre trend | Identify recent growth in content categories. |

---

## 10. Functional Availability

The pipeline runs on Mondays and Fridays at 8:00 a.m. through EventBridge. After each execution:

1. Bronze is updated with new data.
2. Silver is triggered automatically.
3. Silver invokes Gold.
4. Gold recreates the analytical tables.
5. Power BI can be manually refreshed from Desktop.

In a production scenario, the dashboard can be published to Power BI Service and refreshed through Power BI Gateway after each pipeline run.

---

## 11. Functional Limitations

- TMDb is an external source and its metrics do not directly represent the platform’s internal user behavior.
- The solution analyzes market popularity, not actual internal consumption.
- Catalog decisions should complement these results with licensing costs, rights availability, and editorial strategy.
- Power BI Desktop requires manual refresh.
- Automatic production refresh requires Power BI Service and Gateway.
- The solution does not implement personalized recommendations by user.

---

## 12. Glossary

| Term | Definition |
|---|---|
| Catalog | Set of movies available or considered for a streaming platform. |
| TMDb | External data source for movie information. |
| Popularity | TMDb metric that approximates movie visibility or interest. |
| Average rating | Average user rating for a movie in TMDb. |
| Vote volume | Number of votes recorded for a movie. |
| Bronze | Raw data layer. |
| Silver | Clean and structured data layer. |
| Gold | Business analytical data layer. |
| Athena | Service for querying S3 data with SQL. |
| Power BI | Tool for building executive dashboards. |
| Dashboard | Visual view with key indicators for decision-making. |

---

## 13. Conclusion

The system converts external TMDb data into useful information for the catalog management of a streaming platform. The Gold layer and executive dashboard help identify attractive genres, recommendable movies, overexposed content, and recent trends that can support commercial and editorial decisions.
