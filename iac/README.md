# Infrastructure as Code

This folder contains the CloudFormation template used to define the main AWS infrastructure for the StreamSight TMDb Analytics project.

## File

- `cloudformation_tmdb_datalake.yml`: CloudFormation template for the serverless data lake infrastructure.

## Infrastructure included

The template defines the following components:

- Amazon S3 bucket for the data lake.
- Bronze, Silver and Gold prefixes inside the bucket.
- AWS Lambda functions:
  - `tmdb_to_bronze`
  - `bronce_tmdb_to_silver`
  - `silver_tmdb_to_gold`
- EventBridge Scheduler for automated Bronze ingestion.
- S3 Event Notification to trigger the Silver Lambda when a new Bronze file is created.
- AWS Secrets Manager secret for TMDb API configuration.
- AWS Glue database.
- AWS Glue crawler for the Silver layer.
- Amazon Athena workgroup.
- IAM roles and policies required by Lambda, Glue and EventBridge Scheduler.

## Important notes

This template creates the infrastructure shell and placeholder Lambda code.

After deploying the stack, replace the placeholder Lambda code with the actual project code located in:

- `src/lambdas/tmdb_to_bronze/lambda_function.py`
- `src/lambdas/bronce_tmdb_to_silver/lambda_function.py`
- `src/lambdas/silver_tmdb_to_gold/lambda_function.py`

Do not commit real API keys, AWS access keys or secrets to the repository.

The TMDb API key should be provided as a CloudFormation parameter and stored in AWS Secrets Manager.

## Suggested deployment command

```bash
aws cloudformation deploy \
  --template-file iac/cloudformation_tmdb_datalake.yml \
  --stack-name streamsight-tmdb-dev \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    TmdbApiKey=YOUR_TMDB_API_KEY \
    DataLakeBucketName=YOUR_UNIQUE_BUCKET_NAME
```

## Suggested validation

After deployment, validate the following:

1. The S3 bucket exists.
2. The three Lambda functions exist.
3. The EventBridge schedule exists and targets `tmdb_to_bronze`.
4. The S3 notification is configured for the Bronze prefix.
5. The Glue database `db_movies_tmdb` exists.
6. The Glue crawler `crawler-movies-silver` exists.
7. Athena can store query results in the `athena/` S3 prefix.
