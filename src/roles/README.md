# AWS IAM Roles and Policies Documentation

This directory (`src/roles`) contains JSON files defining the AWS Identity and Access Management (IAM) policies and roles used in the movie data pipeline. These roles enforce the principle of least privilege for each component of the system.

## Main Pipeline Roles

### 1. Ingestion (TMDb → Bronze)
**File:** `lambdaFunction-role-m0t0i3rf.json` (and `a.json` used for definitions/testing)
*   **Purpose:** Execution role for the `tmdb_to_bronze` Lambda function.
*   **Permissions:**
    *   `secretsmanager:GetSecretValue`: To read the TMDb API Key and credentials from AWS Secrets Manager.
    *   `s3:PutObject`: To write raw data (JSON/NDJSON files) into the `1bronce/` prefix of the project's S3 bucket.
    *   `logs:CreateLogGroup`, `logs:PutLogEvents`: To emit logs to CloudWatch.

### 2. Transformation and Quality (Bronze → Silver)
**File:** `bronce_tmdb_to_silver-role-fcsfyviv.json`
*   **Purpose:** Execution role for the `bronce_tmdb_to_silver` Lambda function.
*   **Permissions:**
    *   `s3:GetObject` (Prefix `1bronce/`): Read raw data.
    *   `s3:PutObject` (Prefix `2silver/`): Write clean, filtered data in Parquet format.
    *   `s3:ListBucket`: Check for the existence of objects or partitions.
    *   `lambda:InvokeFunction`: To asynchronously trigger the next Lambda (`silver_tmdb_to_gold`) after finishing its execution.
    *   CloudWatch logs.

### 3. Aggregation and Business Logic (Silver → Gold)
**File:** `Rol_Lambda_Capa_Oro.json`
*   **Purpose:** Execution role for the `silver_tmdb_to_gold` Lambda function, which interacts heavily with Athena and Glue.
*   **Permissions (Modified Policy):**
    *   **`S3ReadWriteAccess`**: Allows listing, reading, and deleting objects (for pre-cleaning with `DROP TABLE` and `clean_s3_prefix`), and writing CTAS query results to the `3gold/` prefix and the temporary Athena query results path.
    *   **`AthenaGlueQueryAccess`**: Allows starting (`StartQueryExecution`), monitoring (`GetQueryExecution`), and retrieving results (`GetQueryResults`) in Athena, as well as operating on the Glue Data Catalog (creating/modifying tables and partitions).
    *   **`CloudWatchLogsAccess`**: Log writing.

### 4. Glue/Athena Read Access (AWS Glue Service Role)
**File:** `AWSGlueServiceRole-read-silver.json`
*   **Purpose:** Role assumed by analytical services (such as AWS Glue Crawlers) or Athena itself to access the `db_movies_tmdb` database and the Silver/Gold data in S3 for schema discovery.

### 5. Orchestration (EventBridge)
**File:** `Amazon_EventBridge_Scheduler_LAMBDA_2103acd130.json`
*   **Purpose:** Role assigned to the AWS EventBridge Scheduler.
*   **Permissions:** Allows the `lambda:InvokeFunction` action on a scheduled basis (e.g., daily) to trigger the first Lambda in the pipeline.

## AWS Service-Linked Roles
These roles are auto-generated or used internally by AWS for account and resource management:

*   **`AWSServiceRoleForResourceExplorer.json`**: Used by AWS Resource Explorer to discover and index resources across the account.
*   **`AWSServiceRoleForSupport.json`**: Allows the AWS Support team to access resources and APIs (read-only) for troubleshooting purposes.
*   **`AWSServiceRoleForTrustedAdvisor.json`**: Used by AWS Trusted Advisor to evaluate infrastructure, costs, and security, providing recommendations.
