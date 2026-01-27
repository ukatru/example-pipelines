# Static File & Asset Parameter Analysis: Impact of Prefixed params_schema

## Executive Summary

**CRITICAL FINDING**: Changing `params_schema` to prefixed names (`asset_name.param_name`) will **BREAK** static file jobs unless we handle migration and backward compatibility.

---

## Current Architecture

### 1. **Static Assets (Files with assets, no jobs)**

**Storage**: `asset_metadata` table
- `file_loc`: Path to YAML file
- `file_hash`: MD5 hash of file content
- `params_schema`: Per-asset parameter schema (JSONB)

**Parameter Extraction** (`sync_factory.py:182-210`):
```python
def extract_params_from_asset(asset_conf: Dict[str, Any]) -> Set[str]:
    """Extracts parameter names by parsing {{ params.xxx }} patterns"""
    # Returns: {"source_bucket", "source_path", "target_bucket"}
```

**Storage Format** (`sync_factory.py:320-327`):
```python
asset_params_schema = {
    "type": "object",
    "properties": {
        "source_bucket": {"type": "string"},
        "source_path": {"type": "string"},
        "target_bucket": {"type": "string"}
    }
}
```

**Key Point**: Static assets store **simple parameter names** (no asset prefix) in `asset_metadata.params_schema`.

---

### 2. **Static Jobs (Files with jobs section)**

**Storage**: `etl_job_definition` table
- `params_schema`: Job-level parameter schema (JSONB)
- `yaml_content`: Full YAML content (including `params_schema` and `ops_config`)

**Example** (`phase2_test_cross_ref_static.yaml`):
```yaml
jobs:
  - name: phase2_cross_ref_static_job
    params_schema:
      source_path: "string!|/upload"      # Simple names
      source_pattern: "string!|.*\\.csv"
      target_bucket: "string!|my-dagster-poc"
    job_overrides:
      target_bucket: "my-dagster-poc"    # Shared defaults
    ops_config:
      phase2_cross_ref_asset_1:
        source_path: "/data/sales/input"  # Per-asset override
        source_pattern: "sales_.*\\.csv"
```

**Sync Process** (`sync_factory.py:62-66`):
```python
params_shorthand = config.get("params_schema") or job_conf.get("params_schema")
params_schema = parse_shorthand(params_shorthand)  # Converts to JSON schema
# Stored in etl_job_definition.params_schema as simple names
```

**Key Point**: Static jobs store **simple parameter names** in `etl_job_definition.params_schema`.

---

### 3. **UI-Created Jobs (Multi-asset selection)**

**Current Flow**:
1. **Discovery** (`inspect_selection_params`): Returns prefixed names for UI
2. **Creation** (`create_job_definition`): Converts prefixed → `ops_config`, stores simple names in `params_schema`
3. **Operations Page**: Shows simple names (can't tell which asset)

**Proposed Flow**:
1. **Discovery**: Returns prefixed names (same)
2. **Creation**: Converts prefixed → `ops_config`, stores **prefixed names** in `params_schema`
3. **Operations Page**: Shows prefixed names (clear which asset)

---

## The Problem: Inconsistency

### ❌ **Scenario 1: Static Job with Simple params_schema**

**File**: `phase2_test_cross_ref_static.yaml`
```yaml
jobs:
  - name: phase2_cross_ref_static_job
    params_schema:
      source_path: "string!"      # Simple name
      target_bucket: "string!"
    ops_config:
      phase2_cross_ref_asset_1:
        source_path: "/data/sales/input"
```

**Current Behavior**:
- `etl_job_definition.params_schema` = `{"source_path": "string!", "target_bucket": "string!"}`
- Operations page shows: `source_path`, `target_bucket` (simple names)
- ✅ Works: Users see simple names, `ops_config` handles per-asset overrides

**After Change (Prefixed params_schema)**:
- If we change UI-created jobs to prefixed, but static jobs stay simple:
  - **Inconsistency**: Some jobs show prefixed, others show simple
  - **Confusion**: Users don't know which format to expect

---

### ❌ **Scenario 2: Creating Job from Static Assets**

**File**: `ui_test_graph_a.yaml` (static assets, no jobs)
```yaml
assets:
  - name: sales_ingestion_asset
    source:
      configs:
        bucket_name: "{{ params.source_bucket }}"
        prefix: "{{ params.source_path }}"
```

**Current Flow**:
1. `inspect_selection_params` queries `asset_metadata.params_schema`
2. Finds: `{"type": "object", "properties": {"source_bucket": {...}, "source_path": {...}}}`
3. Returns prefixed: `["sales_ingestion_asset.source_bucket", "sales_ingestion_asset.source_path"]`
4. User creates job → Backend converts to `ops_config`, stores simple names in `params_schema`

**After Change (Prefixed params_schema)**:
1. Same discovery (returns prefixed)
2. User creates job → Backend stores **prefixed names** in `params_schema`
3. ✅ Works: Consistent with UI-created jobs

**BUT**: What about existing static assets?
- `asset_metadata.params_schema` has simple names
- When discovered, we prefix them for UI
- When job is created, we store prefixed in `params_schema`
- ✅ This works because we're transforming during job creation

---

### ❌ **Scenario 3: Static Job Already in Database**

**Problem**: Existing static jobs in DB have simple `params_schema`:
```json
{
  "source_path": "string!",
  "target_bucket": "string!"
}
```

**After Change**:
- New UI-created jobs: Prefixed `params_schema`
- Existing static jobs: Simple `params_schema`
- **Operations Page**: Must handle both formats

**Solution**: Operations page must be **backward compatible**:
```python
def display_params_schema(params_schema):
    if not params_schema:
        return []
    
    # Check if params are prefixed (new format) or simple (old format)
    has_prefixed = any('.' in key for key in params_schema.keys())
    
    if has_prefixed:
        # New format: Show prefixed names
        return [{"name": key, "asset": key.split('.')[0], ...} for key in params_schema.keys()]
    else:
        # Old format: Show simple names (backward compatibility)
        return [{"name": key, "asset": None, ...} for key in params_schema.keys()]
```

---

## Critical Questions

### ❓ **Question 1: Should Static Jobs Use Prefixed params_schema?**

**Option A: Yes (Consistent)**
- Migrate all static jobs to prefixed `params_schema`
- **Pros**: Consistent across all jobs
- **Cons**: Requires migration script, breaks existing static jobs temporarily

**Option B: No (Backward Compatible)**
- Keep static jobs with simple `params_schema`
- UI-created jobs use prefixed `params_schema`
- **Pros**: No migration needed, backward compatible
- **Cons**: Inconsistent user experience

**Option C: Hybrid (Smart Detection)**
- If job has `ops_config` → Use prefixed `params_schema` (multi-asset job)
- If job has no `ops_config` → Use simple `params_schema` (single-asset or shared params)
- **Pros**: Best of both worlds
- **Cons**: More complex logic

**Recommendation**: **Option C (Hybrid)** - Detect based on `ops_config` presence.

---

### ❓ **Question 2: How to Handle Static Asset params_schema?**

**Current**: `asset_metadata.params_schema` has simple names
**Discovery**: We prefix them for UI (`inspect_selection_params`)
**Job Creation**: We store prefixed in `params_schema`

**Question**: Should we also update `asset_metadata.params_schema` to prefixed?

**Answer**: **NO** - Keep `asset_metadata.params_schema` as simple names because:
1. It's per-asset metadata (not job-level)
2. Asset definitions use simple names: `{{params.source_bucket}}`
3. We only prefix when aggregating for job discovery

---

### ❓ **Question 3: Shared vs Per-Asset Parameters**

**Current Static Job Example**:
```yaml
params_schema:
  target_bucket: "string!"      # Shared (used by all assets)
  source_path: "string!"         # Shared (but overridden per-asset)
ops_config:
  phase2_cross_ref_asset_1:
    source_path: "/data/sales/input"  # Per-asset override
```

**After Change**:
```yaml
params_schema:
  target_bucket: "string!"                    # Shared (no prefix)
  phase2_cross_ref_asset_1.source_path: "string!"  # Per-asset (prefixed)
  phase2_cross_ref_asset_2.source_path: "string!"  # Per-asset (prefixed)
ops_config:
  phase2_cross_ref_asset_1:
    source_path: "/data/sales/input"
```

**Logic**:
- If param appears in `ops_config` for specific asset → Prefixed in `params_schema`
- If param only in `job_overrides` (shared) → Simple name in `params_schema`

---

## Migration Strategy

### **Phase 1: Backward Compatibility (Immediate)**

1. **Operations Page**: Handle both formats
   ```python
   def get_params_for_display(params_schema, ops_config):
       if not params_schema:
           return []
       
       # Check format
       has_prefixed = any('.' in key for key in params_schema.keys())
       
       if has_prefixed:
           # New format: Prefixed names
           return parse_prefixed_schema(params_schema, ops_config)
       else:
           # Old format: Simple names (backward compatible)
           return parse_simple_schema(params_schema, ops_config)
   ```

2. **Job Creation**: Always store prefixed (new jobs)
3. **Job Updates**: Convert simple → prefixed if `ops_config` exists

### **Phase 2: Migration (Optional)**

1. **Migration Script**: Convert existing static jobs
   ```python
   def migrate_static_job_to_prefixed(job_def):
       if not job_def.params_schema:
           return
       
       # Check if already prefixed
       has_prefixed = any('.' in key for key in job_def.params_schema.keys())
       if has_prefixed:
           return  # Already migrated
       
       # Convert simple → prefixed based on ops_config
       if job_def.yaml_content:
           yaml_data = yaml.safe_load(job_def.yaml_content)
           ops_config = yaml_data.get("jobs", [{}])[0].get("ops_config", {})
           
           # Build prefixed params_schema
           new_schema = {}
           for asset_name, asset_params in ops_config.items():
               for param_name in asset_params.keys():
                   prefixed_key = f"{asset_name}.{param_name}"
                   new_schema[prefixed_key] = job_def.params_schema.get(param_name, "string!")
           
           # Add shared params (not in ops_config)
           for param_name, param_type in job_def.params_schema.items():
               if param_name not in [p for ops in ops_config.values() for p in ops.keys()]:
                   new_schema[param_name] = param_type
           
           job_def.params_schema = new_schema
   ```

---

## Impact Assessment

### ✅ **What Works (No Changes Needed)**

1. **Static Asset Discovery**: Already prefixes for UI ✅
2. **Job Creation from Static Assets**: Will work with prefixed `params_schema` ✅
3. **Dagster Runtime**: Uses `ops_config` structure (unchanged) ✅
4. **Asset Definitions**: Use simple names `{{params.xxx}}` (unchanged) ✅

### ⚠️ **What Breaks (Needs Fixes)**

1. **Operations Page**: Must handle both simple and prefixed formats
2. **Static Job Sync**: Should detect and convert to prefixed if `ops_config` exists
3. **Parameter Updates**: Must handle both formats when updating

### 🔧 **What Needs Changes**

1. **`create_job_definition` / `update_job_definition`**: Store prefixed `params_schema`
2. **`get_pipeline` / Operations Page**: Handle both formats
3. **`update_pipeline_params`**: Accept prefixed names, split to `ops_config`
4. **`sync_job_definitions`**: Optionally convert static jobs to prefixed

---

## Recommended Approach

### **Hybrid Strategy: Smart Format Detection**

1. **New UI-Created Jobs**: Always use prefixed `params_schema`
2. **Static Jobs**: 
   - If `ops_config` exists → Convert to prefixed `params_schema` during sync
   - If no `ops_config` → Keep simple `params_schema` (shared params only)
3. **Operations Page**: Handle both formats gracefully
4. **Migration**: Optional script to convert existing static jobs

### **Implementation Priority**

1. **P0 (Critical)**: Backward compatibility in Operations Page
2. **P1 (High)**: Prefixed `params_schema` for new UI-created jobs
3. **P2 (Medium)**: Auto-convert static jobs with `ops_config` to prefixed
4. **P3 (Low)**: Migration script for existing static jobs

---

## Conclusion

**Answer**: The proposed change (prefixed `params_schema`) will **NOT break** static files if we:
1. ✅ Maintain backward compatibility in Operations Page
2. ✅ Keep `asset_metadata.params_schema` as simple names (per-asset metadata)
3. ✅ Convert static jobs to prefixed only if they have `ops_config`
4. ✅ Handle both formats gracefully in all parameter-related endpoints

**The key insight**: `params_schema` is UI metadata, not runtime metadata. Dagster uses `ops_config` structure, which remains unchanged. We can safely change `params_schema` format as long as we handle backward compatibility.
