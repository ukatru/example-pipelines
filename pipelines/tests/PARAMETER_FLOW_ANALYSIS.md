# Parameter Flow Analysis: Current vs Proposed

## Current Flow (What We Have Now)

### 1. **Parameter Discovery** (`inspect_selection_params`)
- Returns: `asset_name.param_name` (prefixed) for UI clarity
- Example: `["sales_ingestion_asset.source_bucket", "marketing_ingestion_asset.source_bucket"]`

### 2. **Job Creation/Update** (`create_job_definition` / `update_job_definition`)
- **Input**: `parameter_values` with prefixed keys: `{"sales_ingestion_asset.source_bucket": "value"}`
- **Transformation**: 
  - Split prefixed → `ops_config: {sales_ingestion_asset: {source_bucket: "value"}}`
  - Simple params → `parameter_values: {}` (job-level shared)
- **YAML Output**:
  ```yaml
  params_schema:
    source_bucket: "string!"  # Simple names (for Dagster compatibility)
  ops_config:
    sales_ingestion_asset:
      source_bucket: "value"
  ```

### 3. **Operations Page** (`get_pipeline` in `pipelines.py`)
- Reads `params_schema` from `job_def.params_schema` (simple names)
- Reads `parameter_values` from `ETLJobParameter.config_json` (simple names)
- **Problem**: UI shows simple names, users can't tell which asset each param belongs to

---

## Proposed Flow (What User Wants)

### 1. **Parameter Discovery** (Same)
- Returns: `asset_name.param_name` (prefixed) for UI clarity
- ✅ **No change needed**

### 2. **Job Creation/Update** (Modified)
- **Input**: `parameter_values` with prefixed keys: `{"sales_ingestion_asset.source_bucket": "value"}`
- **Transformation**: 
  - Split prefixed → `ops_config: {sales_ingestion_asset: {source_bucket: "value"}}`
  - Simple params → `parameter_values: {}` (job-level shared)
- **YAML Output**:
  ```yaml
  params_schema:
    sales_ingestion_asset.source_bucket: "string!"  # Prefixed names (for UI clarity)
    marketing_ingestion_asset.source_bucket: "string!"
  ops_config:
    sales_ingestion_asset:
      source_bucket: "value"
  ```

### 3. **Operations Page** (Modified)
- Reads `params_schema` from `job_def.params_schema` (prefixed names)
- Reads `parameter_values` from `ETLJobParameter.config_json` (prefixed names)
- **Benefit**: UI shows prefixed names, users can differentiate parameters by asset

---

## Key Questions to Resolve

### ❓ Question 1: How does Dagster resolve parameters at runtime?

**Current Understanding:**
- Dagster doesn't use `params_schema` - it's just metadata
- Dagster uses the actual parameter values passed in `run_config`
- Asset definitions use `{{params.source_bucket}}` (simple names)
- `job_factory.py` merges `ops_config` into `run_config` with prefixed keys: `__nexus_ops__{asset_name}__{param_name}`

**Answer**: Dagster resolution happens via `job_factory.py` which:
1. Takes `ops_config` from YAML
2. Converts to `__nexus_ops__{asset_name}__{param_name}` in `run_config`
3. Assets access via `context.resources.params.config.get("__nexus_ops__{asset_name}__{param_name}")`

**Conclusion**: `params_schema` format doesn't affect Dagster runtime - it's purely for UI display.

---

### ❓ Question 2: What happens when user edits parameters in Operations page?

**Current Flow:**
1. User sees simple names: `source_bucket`
2. User edits value
3. Backend receives: `{"source_bucket": "new_value"}`
4. Backend needs to know: which asset does this belong to?

**Proposed Flow:**
1. User sees prefixed names: `sales_ingestion_asset.source_bucket`
2. User edits value
3. Backend receives: `{"sales_ingestion_asset.source_bucket": "new_value"}`
4. Backend splits: `ops_config: {sales_ingestion_asset: {source_bucket: "new_value"}}`

**Conclusion**: Prefixed names in `params_schema` make it clear which asset each parameter belongs to, even when editing.

---

### ❓ Question 3: What about shared/job-level parameters?

**Scenario**: Both assets use `target_bucket` (same value for both)

**Current Approach:**
- Store in `parameter_values` (simple name): `{"target_bucket": "shared-value"}`
- Don't include in `ops_config`
- Both assets read from `{{params.target_bucket}}`

**Proposed Approach:**
- Still store in `parameter_values` (simple name): `{"target_bucket": "shared-value"}`
- `params_schema` can show: `target_bucket: "string!"` (simple name, no prefix)
- OR show both: `sales_ingestion_asset.target_bucket` and `marketing_ingestion_asset.target_bucket` (if user wants to override per-asset)

**Conclusion**: Need to decide:
- **Option A**: Shared params show as simple names, per-asset params show as prefixed
- **Option B**: All params show as prefixed (even if shared), user can choose to override per-asset

---

### ❓ Question 4: How do we handle parameter updates from Operations page?

**Current Implementation** (`update_pipeline_params` in `pipelines.py`):
- Accepts flat dict: `{"param1": "value1", "param2": "value2"}`
- Stores in `ETLJobParameter.config_json`
- Extracts `_ops_config` if present

**Proposed Implementation**:
- Accept prefixed names: `{"sales_ingestion_asset.source_bucket": "value1"}`
- Split into `ops_config` structure
- Store simple names in `parameter_values` (for shared params)
- Store per-asset in `_ops_config`

**Challenge**: How do we know if a prefixed param should be:
1. Per-asset override (goes to `ops_config`)
2. Shared param (goes to `parameter_values`)

**Solution**: 
- If param appears in `ops_config` in YAML → it's per-asset
- If param only appears in `params_schema` (simple name) → it's shared
- When user edits prefixed param → always update `ops_config`
- When user edits simple param → update `parameter_values`

---

## Recommended Approach

### ✅ **Hybrid Approach: Prefixed in Schema, Split in Storage**

1. **`params_schema` in YAML**: Contains prefixed names for UI clarity
   ```yaml
   params_schema:
     sales_ingestion_asset.source_bucket: "string!"
     marketing_ingestion_asset.source_bucket: "string!"
     target_bucket: "string!"  # Shared param (no prefix)
   ```

2. **`ops_config` in YAML**: Contains split structure for Dagster
   ```yaml
   ops_config:
     sales_ingestion_asset:
       source_bucket: "value"
   ```

3. **Storage in DB**:
   - `job_def.params_schema`: Prefixed names (for UI)
   - `ETLJobParameter.config_json`: 
     - Simple names in root (shared params)
     - `_ops_config`: Per-asset structure

4. **Operations Page Display**:
   - Show prefixed names from `params_schema`
   - When user edits, send prefixed names
   - Backend splits prefixed → `ops_config` structure

5. **Runtime (Dagster)**:
   - `job_factory.py` reads `ops_config` from YAML
   - Converts to `__nexus_ops__{asset_name}__{param_name}` in `run_config`
   - Assets access via `context.resources.params.config.get(...)`

---

## Implementation Changes Needed

### 1. **`create_job_definition` / `update_job_definition`** (`graphs.py`)
- **Change**: Build `params_schema` with prefixed names (not simple names)
- **Keep**: `ops_config` structure as-is
- **Store**: Prefixed `params_schema` in `job_def.params_schema`

### 2. **`update_pipeline_params`** (`pipelines.py`)
- **Change**: Accept prefixed parameter names
- **Change**: Split prefixed names into `ops_config` structure
- **Keep**: Simple names in `parameter_values` for shared params

### 3. **Operations Page UI** (Frontend)
- **Change**: Display prefixed parameter names from `params_schema`
- **Change**: Send prefixed names when updating parameters
- **Keep**: Form structure (just change labels/keys)

---

## Benefits

✅ **UI Clarity**: Users can see which asset each parameter belongs to
✅ **Dagster Compatibility**: Runtime still uses simple names via `ops_config`
✅ **Backward Compatible**: Can still support simple names for shared params
✅ **Flexible**: Users can override per-asset or use shared values

---

## Potential Issues

⚠️ **Issue 1**: What if user deletes a prefixed param from UI?
- **Solution**: Remove from `ops_config` for that asset

⚠️ **Issue 2**: What if user adds a new prefixed param?
- **Solution**: Add to `ops_config` for that asset, update `params_schema`

⚠️ **Issue 3**: What if `params_schema` has both prefixed and simple names?
- **Solution**: Simple names = shared params, prefixed names = per-asset params

---

## Conclusion

**YES, we're on the same page!** The approach makes sense:
1. `params_schema` contains prefixed names for UI clarity
2. `ops_config` contains split structure for Dagster
3. Backend splits prefixed names → `ops_config` when saving
4. Operations page shows prefixed names for user clarity

The key insight: `params_schema` is metadata for UI, not for Dagster runtime. Dagster uses `ops_config` structure, which we already handle correctly.
