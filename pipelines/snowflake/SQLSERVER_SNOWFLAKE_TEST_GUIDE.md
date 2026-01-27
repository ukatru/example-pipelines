# SQL Server to Snowflake Operator Test Guide

## Overview
This guide helps you test the enhanced SQL Server to Snowflake operator with:
- **Auto Table Creation**: Automatically creates Snowflake tables from SQL Server schema
- **Type Validation**: Validates column types before data transfer
- **Schema Inference**: Reads SQL Server table structure automatically

## Test Files

1. **`sqlserver_snowflake_simple.yaml`** - Start here! Simple test with auto table creation
2. **`sqlserver_snowflake_with_sql.yaml`** - Alternative using custom SQL query

## Prerequisites

### 1. SQL Server Setup
- SQL Server instance accessible
- Source table exists (e.g., `AdventureWorksSales`)
- Connection configured in `connections/` directory

### 2. Snowflake Setup
- Snowflake account accessible
- Connection configured in `connections/` directory
- Target table will be auto-created (no manual DDL needed!)

### 3. Connection Names
Update connection names in the YAML files:
- `SQLSERVER` - Your SQL Server connection name
- `SNOWFLAKE` - Your Snowflake connection name

## Test Scenarios

### Test 1: Auto Table Creation (Recommended)
**File**: `sqlserver_snowflake_simple.yaml`

**Configuration**:
```yaml
source:
  type: SQLSERVER
  configs:
    table_name: "YourTableName"  # Must use table_name (not custom SQL)
    schema_name: "dbo"  # Optional
    auto_create_table: true  # NEW FEATURE
    type_mismatch_failure: true  # NEW FEATURE
```

**What it does**:
1. Reads SQL Server table schema from `INFORMATION_SCHEMA`
2. Maps SQL Server types to Snowflake types (e.g., `int` → `NUMBER`, `varchar` → `VARCHAR`)
3. Creates Snowflake table automatically if it doesn't exist
4. Validates types before data transfer
5. Transfers data in chunks

**Expected Result**:
- ✅ Table created in Snowflake with correct schema
- ✅ Data transferred successfully
- ✅ Types match between SQL Server and Snowflake

### Test 2: Custom SQL Query
**File**: `sqlserver_snowflake_with_sql.yaml`

**Configuration**:
```yaml
source:
  type: SQLSERVER
  configs:
    sql: "SELECT * FROM dbo.YourTable WHERE ..."  # Custom SQL
    auto_create_table: false  # Can't auto-create from custom SQL
```

**What it does**:
- Uses custom SQL query instead of table_name
- Note: Auto-create requires `table_name` (schema inference needs table name)
- You can create table manually via `sql_pre` if needed

## Type Mapping Examples

The operator automatically maps SQL Server types to Snowflake:

| SQL Server | Snowflake |
|------------|-----------|
| `int` | `NUMBER` |
| `varchar(100)` | `VARCHAR(100)` |
| `datetime` | `TIMESTAMP_NTZ` |
| `decimal(18,2)` | `NUMBER(18,2)` |
| `bit` | `BOOLEAN` |
| `nvarchar(max)` | `VARCHAR(16777216)` |

See `type_mappings.py` for complete mapping.

## Troubleshooting

### Error: "Could not retrieve schema for table"
**Cause**: Table doesn't exist in SQL Server or wrong schema name
**Fix**: Verify table name and schema in source config

### Error: "Column type validation failed"
**Cause**: Types in Snowflake table don't match expected types
**Fix**: 
- Set `auto_create_table: true` to let operator create table
- Or fix Snowflake table schema manually
- Or set `type_mismatch_failure: false` to skip validation

### Error: "Table already exists"
**Cause**: Table exists but `auto_create_table: true` is set
**Fix**: This is OK - operator skips creation if table exists (uses `IF NOT EXISTS`)

### Error: "Could not get Snowflake schema"
**Cause**: Table doesn't exist and `auto_create_table: false`
**Fix**: Set `auto_create_table: true` or create table manually

## Validation Features

### Type Validation (`type_mismatch_failure: true`)
- Validates column types before data transfer
- Compares SQL Server types with Snowflake types
- Fails early if types are incompatible
- Provides clear error messages

### Column Validation
- Checks if all SQL Server columns exist in Snowflake
- Reports missing columns
- Reports type mismatches

## Performance Tips

1. **Chunk Size**: Adjust `rows_chunk` based on table size
   - Small tables: 5000-10000
   - Large tables: 10000-50000

2. **Auto Create**: Use `auto_create_table: true` for first run
   - Subsequent runs will skip creation (table exists)
   - Faster than manual DDL

3. **Type Validation**: Enable for first run, disable for subsequent runs
   - First run: `type_mismatch_failure: true` (validate)
   - Subsequent runs: `type_mismatch_failure: false` (skip validation)

## Example: Full Migration Workflow

```yaml
# Step 1: Initial load with auto-create
assets:
  - name: initial_load
    source:
      type: SQLSERVER
      configs:
        table_name: "SalesData"
        auto_create_table: true  # Create table
        type_mismatch_failure: true  # Validate types
    target:
      type: SNOWFLAKE
      configs:
        table_name: "SALES_DATA"

# Step 2: Incremental load (table exists)
assets:
  - name: incremental_load
    source:
      type: SQLSERVER
      configs:
        sql: "SELECT * FROM SalesData WHERE UpdatedDate >= '{{ partition_start }}'"
        auto_create_table: false  # Table exists
        type_mismatch_failure: false  # Skip validation
    target:
      type: SNOWFLAKE
      configs:
        table_name: "SALES_DATA"
```

## Next Steps

1. Update connection names in YAML files
2. Update table names to match your SQL Server tables
3. Run the pipeline in Dagster
4. Check Snowflake for auto-created table
5. Verify data was transferred correctly
