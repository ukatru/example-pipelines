# S3-Snowflake Operator Test Cases

## Overview
Comprehensive test cases for the S3-Snowflake operator covering all features and edge cases.

## Test Files

1. **`s3_snowflake_simple.yaml`** - Start here! Simple basic test
2. **`s3_snowflake_comprehensive.yaml`** - All test cases with all features

## Test Environment Setup

### Snowflake Configuration
- **Stage**: `MY_DAGSTER_POC_STAGE`
- **Database**: `DAGSTER_POC`
- **Schema**: `DATA_ANALYTICS`
- **Connection**: `SNOWFLAKE` (update to match your connection name in connections YAML)
  - Common names: `SNOWFLAKE`, `snowflake_prod`, `snowflake_conn`
  - Check `/home/ukatru/github/example-pipelines/connections/` for available connections

### S3 Configuration
- **Bucket**: `my-dagster-poc`
- **Connection**: `S3` (default profile)

## Test Cases

### Test 1: Basic COPY INTO
**Asset**: `test_basic_copy_into`
**Purpose**: Verify basic COPY INTO functionality
**Source**: Single CSV file
**Target**: Table `TEST_BASIC_COPY`
**Config**:
- `match_columns: true`
- `force: true`
- `on_error: SKIP_FILE`
- `schema_strategy: fail`

**Expected**: Data loads successfully using `MATCH_BY_COLUMN_NAME`

---

### Test 2: Column Name Matching with Validation
**Asset**: `test_column_name_match`
**Purpose**: Verify column matching by name with validation
**Source**: Multiple CSV files from prefix
**Target**: Table `TEST_COLUMN_MATCH`
**Config**:
- `column_match_config: column_name_match`
- `column_mismatch_failure: true`

**Expected**: 
- Validates CSV headers match target table columns
- Fails if columns don't match
- Case-insensitive matching

**Test Scenarios**:
1. ✅ CSV columns match target → Success
2. ❌ CSV has extra columns → Fail
3. ❌ CSV missing columns → Fail
4. ❌ Column names differ (case-insensitive) → Success

---

### Test 3: Column Order Matching
**Asset**: `test_column_order_match`
**Purpose**: Verify column matching by position
**Source**: Single CSV file
**Target**: Table `TEST_COLUMN_ORDER`
**Config**:
- `match_columns: false`
- `column_match_config: target_column_order`
- `column_mismatch_failure: true`

**Expected**:
- Validates column count matches
- Fails if count doesn't match
- Position-based matching

**Test Scenarios**:
1. ✅ Column count matches → Success
2. ❌ Column count differs → Fail

---

### Test 4: Schema Strategy - CREATE
**Asset**: `test_schema_create`
**Purpose**: Auto-create table if it doesn't exist
**Source**: Single CSV file
**Target**: Table `TEST_SCHEMA_CREATE` (doesn't exist)
**Config**:
- `schema_strategy: create`

**Expected**:
- Table is created automatically
- Columns inferred from CSV
- Data loads successfully

**Test Scenarios**:
1. ✅ Table doesn't exist → Created and loaded
2. ✅ Table exists → Loads to existing table

---

### Test 5: Schema Strategy - EVOLVE
**Asset**: `test_schema_evolve`
**Purpose**: Auto-add new columns if they exist in source
**Source**: CSV with new columns
**Target**: Table `TEST_SCHEMA_EVOLVE` (exists with fewer columns)
**Config**:
- `schema_strategy: evolve`

**Expected**:
- New columns are added to table
- Existing data preserved
- New data loads successfully

**Test Scenarios**:
1. ✅ CSV has new columns → Columns added, data loaded
2. ✅ CSV matches existing schema → Data loaded

---

### Test 6: Schema Strategy - STRICT
**Asset**: `test_schema_strict`
**Purpose**: Strict schema validation
**Source**: CSV file
**Target**: Table `TEST_SCHEMA_STRICT`
**Config**:
- `schema_strategy: strict`
- `column_mismatch_failure: true`

**Expected**:
- Fails if columns don't match exactly
- No new columns added
- No missing columns allowed

**Test Scenarios**:
1. ✅ Exact match → Success
2. ❌ New columns in CSV → Fail
3. ❌ Missing columns in CSV → Fail

---

### Test 7: Unique Constraint Validation
**Asset**: `test_unique_constraint_check`
**Purpose**: Validate no duplicate rows after load
**Source**: CSV file (may contain duplicates)
**Target**: Table `TEST_UNIQUE_CHECK` (has PK/UK)
**Config**:
- `unique_constraint_check: true`

**Expected**:
- After load, checks for duplicates
- Fails if duplicates found
- Shows duplicate values in error

**Test Scenarios**:
1. ✅ No duplicates → Success
2. ❌ Duplicates found → Fail with error message
3. ✅ No PK/UK in table → Warning, skip validation

---

### Test 8: Parquet Format
**Asset**: `test_parquet_format`
**Purpose**: Load Parquet files
**Source**: Multiple Parquet files
**Target**: Table `TEST_PARQUET`
**Config**:
- `object_type: PARQUET`
- `schema_strategy: create`

**Expected**:
- Parquet files loaded successfully
- Schema inferred from Parquet
- Table created if needed

---

### Test 9: JSON Format
**Asset**: `test_json_format`
**Purpose**: Load JSON files
**Source**: Multiple JSON files
**Target**: Table `TEST_JSON`
**Config**:
- `object_type: JSON`
- `schema_strategy: create`

**Expected**:
- JSON files loaded successfully
- Schema inferred from JSON
- Table created if needed

---

### Test 10: Multiple Files from Prefix
**Asset**: `test_multiple_files`
**Purpose**: Load multiple CSV files from a prefix
**Source**: Multiple CSV files in prefix
**Target**: Table `TEST_MULTI_FILE`
**Config**:
- `prefix: test_data/multi_file/`
- `pattern: .*\.csv`
- `on_error: CONTINUE`

**Expected**:
- All matching files loaded
- Continues on individual file errors
- All successful files loaded

---

### Test 11: Column Mismatch Validation Disabled
**Asset**: `test_column_mismatch_disabled`
**Purpose**: Load with validation disabled
**Source**: CSV with mismatched columns
**Target**: Table `TEST_MISMATCH_DISABLED`
**Config**:
- `column_mismatch_failure: false`

**Expected**:
- Loads even if columns don't match
- No validation error
- Data loads (may have NULLs for missing columns)

---

### Test 12: All Features Combined
**Asset**: `test_all_features`
**Purpose**: Test all features together
**Source**: Multiple CSV files
**Target**: Table `TEST_ALL_FEATURES`
**Config**:
- `match_columns: true`
- `column_match_config: column_name_match`
- `column_mismatch_failure: true`
- `unique_constraint_check: true`
- `schema_strategy: evolve`
- `force: true`

**Expected**:
- All validations run
- Schema evolves if needed
- Duplicates checked
- Data loads successfully

---

## Edge Cases to Test

### CSV Header Detection
1. ✅ CSV with headers → Headers detected
2. ✅ CSV without headers → Warning, skip validation
3. ✅ Empty CSV file → Warning, skip validation
4. ✅ CSV with special characters in headers → Handled correctly
5. ✅ CSV with quoted headers → Parsed correctly

### Column Matching
1. ✅ Case-insensitive matching → Works
2. ✅ Special characters in column names → Handled
3. ✅ Whitespace in column names → Trimmed
4. ✅ Different column order → Works with `column_name_match`
5. ✅ Extra columns in CSV → Fails if `column_mismatch_failure: true`

### Unique Constraint Validation
1. ✅ Table with PK → Validated
2. ✅ Table with UK → Validated
3. ✅ Table with both PK and UK → Both validated
4. ✅ Table without PK/UK → Warning, skip validation
5. ✅ Large table → Performance acceptable

### File Format Handling
1. ✅ CSV with different delimiters → Handled
2. ✅ CSV with/without headers → Handled
3. ✅ Parquet with nested structures → Handled
4. ✅ JSON with arrays → Handled

### Error Handling
1. ✅ Invalid S3 path → Clear error message
2. ✅ Table doesn't exist (fail strategy) → Clear error
3. ✅ Column mismatch → Detailed error with column lists
4. ✅ Duplicate constraint violation → Error with duplicate values
5. ✅ Snowflake connection error → Clear error message

## Test Data Preparation

### Required Test Files in S3

Create the following test files in `s3://my-dagster-poc/test_data/`:

1. **basic_test.csv** - Simple CSV with headers matching target table
2. **column_match/*.csv** - Multiple files with matching columns
3. **order_match.csv** - CSV with columns in specific order
4. **schema_create.csv** - CSV for table creation
5. **schema_evolve.csv** - CSV with new columns
6. **schema_strict.csv** - CSV matching exact schema
7. **unique_check.csv** - CSV that may contain duplicates
8. **parquet/*.parquet** - Parquet files
9. **json/*.json** - JSON files
10. **multi_file/*.csv** - Multiple CSV files
11. **mismatch_test.csv** - CSV with mismatched columns
12. **comprehensive/*.csv** - Files for comprehensive test

### Required Snowflake Tables

Create these tables in `DAGSTER_POC.DATA_ANALYTICS`:

```sql
-- Test tables (create as needed, some will be auto-created)
CREATE TABLE IF NOT EXISTS TEST_BASIC_COPY (
    id INT,
    name VARCHAR(100),
    amount FLOAT,
    created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS TEST_COLUMN_MATCH (
    id INT,
    name VARCHAR(100),
    amount FLOAT,
    created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS TEST_COLUMN_ORDER (
    col1 VARCHAR(50),
    col2 INT,
    col3 FLOAT,
    col4 TIMESTAMP
);

-- Table with PK for unique constraint test
CREATE TABLE IF NOT EXISTS TEST_UNIQUE_CHECK (
    id INT PRIMARY KEY,
    name VARCHAR(100),
    amount FLOAT,
    created_at TIMESTAMP
);

-- Table for evolve test (start with fewer columns)
CREATE TABLE IF NOT EXISTS TEST_SCHEMA_EVOLVE (
    id INT,
    name VARCHAR(100)
);

-- Table for strict test (exact schema)
CREATE TABLE IF NOT EXISTS TEST_SCHEMA_STRICT (
    id INT,
    name VARCHAR(100),
    amount FLOAT,
    created_at TIMESTAMP
);
```

## Running Tests

### Run Simple Test First
```bash
cd /home/ukatru/github/example-pipelines
dagster job execute -j simple_s3_to_snowflake_job
```

### Run Individual Tests
```bash
dagster job execute -j test_basic_job
dagster job execute -j test_column_matching_job
dagster job execute -j test_schema_strategies_job
dagster job execute -j test_validation_job
dagster job execute -j test_file_formats_job
```

### Run All Tests
```bash
dagster job execute -j s3_snowflake_comprehensive_test_job
```

## Success Criteria

Each test should:
1. ✅ Execute without errors (unless testing error cases)
2. ✅ Load expected number of rows
3. ✅ Validate columns correctly (if enabled)
4. ✅ Check constraints correctly (if enabled)
5. ✅ Log clear messages about what's happening
6. ✅ Return proper result structure

## Troubleshooting

### Common Issues

1. **Column mismatch errors**
   - Check CSV headers match target table columns
   - Verify `column_match_config` setting
   - Check case sensitivity

2. **Unique constraint violations**
   - Verify table has PK/UK defined
   - Check for duplicate data in source
   - Review error message for duplicate values

3. **Schema strategy failures**
   - Verify table exists (for fail/evolve/strict)
   - Check inferred schema matches expectations
   - Review logs for schema inference details

4. **File not found**
   - Verify S3 path is correct
   - Check bucket and prefix
   - Verify file exists in S3

5. **Snowflake connection errors**
   - Verify credentials in .env file
   - Check stage exists: `MY_DAGSTER_POC_STAGE`
   - Verify database/schema access
