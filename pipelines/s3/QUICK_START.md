# S3-Snowflake Operator Quick Start Guide

## Prerequisites

1. **Snowflake Setup**:
   - External stage created: `MY_DAGSTER_POC_STAGE`
   - Database: `DAGSTER_POC`
   - Schema: `DATA_ANALYTICS`
   - Credentials in `.env` file

2. **S3 Setup**:
   - Bucket: `my-dagster-poc`
   - Default AWS profile has access

3. **Connection Configuration**:
   - Check `/home/ukatru/github/example-pipelines/connections/` for connection names
   - Update `connection: SNOWFLAKE` in YAML to match your connection name

## Quick Test

### Step 1: Create Test CSV File

Create a simple CSV file in S3:
```bash
# Example CSV content (upload to s3://my-dagster-poc/test_data/simple_test.csv)
id,name,amount,created_at
1,Product A,100.50,2024-01-01 10:00:00
2,Product B,200.75,2024-01-01 11:00:00
3,Product C,150.25,2024-01-01 12:00:00
```

### Step 2: Create Target Table (Optional - will auto-create if schema_strategy: create)

```sql
USE DATABASE DAGSTER_POC;
USE SCHEMA DATA_ANALYTICS;

CREATE TABLE IF NOT EXISTS SIMPLE_TEST (
    id INT,
    name VARCHAR(100),
    amount FLOAT,
    created_at TIMESTAMP
);
```

### Step 3: Update Connection Name

Edit `s3_snowflake_simple_test.yaml`:
- Update `connection: SNOWFLAKE` to match your connection name
- Update `key: "test_data/simple_test.csv"` to your test file path

### Step 4: Run Test

```bash
cd /home/ukatru/github/example-pipelines
dagster job execute -j simple_s3_to_snowflake_job
```

## Test Files Created

1. **`s3_snowflake_simple_test.yaml`** - Minimal test (start here)
2. **`s3_snowflake_comprehensive_test.yaml`** - All test cases
3. **`S3_SNOWFLAKE_TEST_CASES.md`** - Detailed test documentation

## Features to Test

### Basic Features
- ✅ Simple COPY INTO
- ✅ Column name matching
- ✅ Column order matching
- ✅ Multiple files from prefix

### Schema Strategies
- ✅ CREATE (auto-create table)
- ✅ EVOLVE (add new columns)
- ✅ STRICT (exact match required)
- ✅ FAIL (fail if table doesn't exist)

### Validations
- ✅ Column mismatch detection
- ✅ Unique constraint validation

### File Formats
- ✅ CSV
- ✅ Parquet
- ✅ JSON

## Next Steps

1. Run `simple_s3_to_snowflake_job` first
2. If successful, try individual tests from comprehensive test file
3. Review logs for validation messages
4. Check Snowflake table for loaded data
