# Multi-Asset Job Testing Guide

This guide tests various combinations of selecting sales and marketing assets to understand how Dagster's multi-selection works and verify our implementation.

## Test Assets

**Sales Pipeline:**
- `sales_ingestion_asset` (upstream)
  - Parameters: `source_bucket`, `source_path`, `source_pattern`, `target_bucket`
- `sales_transformed_asset` (downstream of `sales_ingestion_asset`)
  - Parameters: `target_bucket` (inherits from upstream)

**Marketing Pipeline:**
- `marketing_ingestion_asset` (upstream)
  - Parameters: `source_bucket`, `source_path`, `source_pattern`, `target_bucket`
- `marketing_analytics_asset` (downstream of `marketing_ingestion_asset`)
  - Parameters: `target_bucket` (inherits from upstream)

## Test Jobs Created

### Python-Based Jobs (`test_multi_asset_job.py`)

1. **`test_multi_asset_explicit`**
   - Selection: `AssetSelection.keys("sales_ingestion_asset", "marketing_ingestion_asset")`
   - Tests: Explicit selection of two assets
   - Expected: 2 assets selected

2. **`test_multi_asset_downstream`**
   - Selection: `AssetSelection.keys("sales_ingestion_asset").downstream() | AssetSelection.keys("marketing_ingestion_asset").downstream()`
   - Tests: Downstream selection (equivalent to `*` syntax)
   - Expected: 4 assets selected (both ingestion + both downstream)

3. **`test_multi_asset_groups`**
   - Selection: `AssetSelection.groups("sales_pipeline") | AssetSelection.groups("marketing_pipeline")`
   - Tests: Group-based selection
   - Expected: All 4 assets selected

4. **`test_multi_asset_union`**
   - Selection: Union of all 4 assets explicitly
   - Tests: Explicit union of multiple assets
   - Expected: 4 assets selected

5. **`test_multi_asset_ingestion_only`**
   - Selection: Only ingestion assets (no downstream)
   - Tests: Selecting upstream assets without downstream
   - Expected: 2 assets selected

6. **`test_multi_asset_downstream_only`**
   - Selection: Only downstream assets
   - Tests: Selecting downstream without upstream
   - Expected: 2 assets selected (but will fail if upstream not materialized)

### YAML-Based Jobs (`test_multi_asset_jobs.yaml`)

1. **`test_multi_asset_explicit_yaml`**
   - Selection: `key: sales_ingestion_asset`, `key: marketing_ingestion_asset`
   - Tests: YAML explicit selection

2. **`test_multi_asset_downstream_yaml`**
   - Selection: `key: sales_ingestion_asset*`, `key: marketing_ingestion_asset*`
   - Tests: YAML downstream selection with `*` syntax
   - **This tests our `*` to `.downstream()` conversion**

3. **`test_multi_asset_groups_yaml`**
   - Selection: `group: sales_pipeline`, `group: marketing_pipeline`
   - Tests: YAML group selection

4. **`test_multi_asset_mixed_yaml`**
   - Selection: `key: sales_ingestion_asset`, `key: marketing_ingestion_asset*`
   - Tests: Mixed selection (explicit + downstream)

5. **`test_multi_asset_all_yaml`**
   - Selection: Both assets with downstream
   - Includes: `ops_config` example with per-asset overrides
   - Tests: Full multi-asset job with `ops_config`

## How to Test

### 1. Run the Test Script

```bash
cd /home/ukatru/github/example-pipelines
python test_multi_asset_jobs.py
```

This will:
- List all available assets
- List all defined jobs
- Test various selection patterns
- Show resolved assets for each pattern
- Display dependency information

### 2. Start Dagster Dev

```bash
cd /home/ukatru/github/example-pipelines
dagster dev
```

Then in the Dagster UI:
1. Navigate to "Jobs" section
2. You should see all test jobs listed
3. Click on each job to see:
   - Which assets are selected
   - The selection logic
   - Job configuration

### 3. Test Job Execution

For each test job:
1. Click "Materialize" in Dagster UI
2. Observe which assets get materialized
3. Verify the selection logic matches expectations

### 4. Test Parameter Resolution

For jobs with `ops_config`:
1. Check how parameters are resolved
2. Verify `ops_config` values are applied correctly
3. Test in operations-pipelines page to see how it's displayed

## Expected Results

### Test 1: Explicit Selection
- **Selected**: `sales_ingestion_asset`, `marketing_ingestion_asset`
- **Parameters**: All 4 params from both assets (with prefixing in UI)
- **ops_config**: Per-asset overrides if provided

### Test 2: Downstream Selection
- **Selected**: All 4 assets (both ingestion + both downstream)
- **Parameters**: All params from ingestion assets (downstream inherit)
- **ops_config**: Can override per asset

### Test 3: Group Selection
- **Selected**: All 4 assets (all in both groups)
- **Parameters**: All params from all assets
- **ops_config**: Can override per asset

## Key Learnings

1. **Dagster's `.downstream()` method**:
   - Automatically includes the selected asset + all downstream dependencies
   - Uses the asset dependency graph (from `ins: { upstream: { key: ... } }`)
   - Works correctly with our `*` syntax conversion

2. **Multi-selection with `|` operator**:
   - Combines multiple selections
   - Each selection is independent
   - Union of all selected assets

3. **Parameter Discovery**:
   - Parameters come from all selected assets
   - Downstream assets inherit from upstream
   - `ops_config` allows per-asset overrides

4. **Operations Page**:
   - Reads from `ETLJobParameter.config_json`
   - Extracts `_ops_config` for per-asset config
   - Shows parameters in UI for management

## Testing Checklist

- [ ] Python jobs load correctly in Dagster
- [ ] YAML jobs load correctly in Dagster
- [ ] `*` syntax converts to `.downstream()` correctly
- [ ] Parameter discovery finds all parameters
- [ ] `ops_config` is saved correctly in job YAML
- [ ] `params_schema` has simple names only
- [ ] Operations page displays parameters correctly
- [ ] Per-asset config works when job runs
- [ ] Multi-asset selection resolves correctly
