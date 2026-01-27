# Comprehensive Parameter Analysis: Static Files, Asset Parameters, Shared vs Per-Asset

## Executive Summary

**Answer**: The proposed change (prefixed `params_schema`) will **NOT break** static files if we implement backward compatibility and smart format detection. However, we need to handle three distinct scenarios carefully.

---

## Three Parameter Sources

### 1. **Static Assets (Files with assets, no jobs)**
- **Storage**: `asset_metadata.params_schema` (per-asset, simple names)
- **Example**: `ui_test_graph_a.yaml` → `sales_ingestion_asset` uses `{{params.source_bucket}}`
- **Current**: Simple names stored: `{"source_bucket": {"type": "string"}}`
- **After Change**: **Keep simple names** (per-asset metadata, not job-level)

### 2. **Static Jobs (Files with jobs section)**
- **Storage**: `etl_job_definition.params_schema` (job-level, simple names)
- **Example**: `phase2_test_cross_ref_static.yaml` → Has `params_schema` and `ops_config`
- **Current**: Simple names: `{"source_path": "string!", "target_bucket": "string!"}`
- **After Change**: **Convert to prefixed IF `ops_config` exists** (hybrid approach)

### 3. **UI-Created Jobs (Multi-asset selection)**
- **Storage**: `etl_job_definition.params_schema` (job-level, should be prefixed)
- **Current**: Simple names (inconsistent with discovery)
- **After Change**: **Always prefixed** (consistent with discovery)

---

## Detailed Analysis

### ✅ **Scenario 1: Static Assets → Job Creation**

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
1. `sync_static_assets()` → Stores in `asset_metadata.params_schema`:
   ```json
   {
     "type": "object",
     "properties": {
       "source_bucket": {"type": "string"},
       "source_path": {"type": "string"}
     }
   }
   ```
2. User selects `sales_ingestion_asset` in UI
3. `inspect_selection_params()` → Queries `asset_metadata.params_schema`
4. Returns prefixed: `["sales_ingestion_asset.source_bucket", "sales_ingestion_asset.source_path"]`
5. User creates job → Backend stores simple names in `params_schema`

**After Change**:
1. Same sync (keeps simple names in `asset_metadata.params_schema`) ✅
2. Same discovery (returns prefixed) ✅
3. User creates job → Backend stores **prefixed names** in `params_schema` ✅
4. Operations page shows prefixed names ✅

**Conclusion**: ✅ **Works perfectly** - No breaking changes needed.

---

### ⚠️ **Scenario 2: Static Job Already in Database**

**File**: `phase2_test_cross_ref_static.yaml` (has jobs section)
```yaml
jobs:
  - name: phase2_cross_ref_static_job
    params_schema:
      source_path: "string!|/upload"
      target_bucket: "string!|my-dagster-poc"
    ops_config:
      phase2_cross_ref_asset_1:
        source_path: "/data/sales/input"
```

**Current State** (in database):
- `etl_job_definition.params_schema` = `{"source_path": "string!", "target_bucket": "string!"}`
- `etl_job_definition.yaml_content` contains `ops_config`

**After Change**:
- **Problem**: Existing static jobs have simple `params_schema`
- **Solution**: **Backward compatibility** + **Auto-conversion**

**Recommended Approach**:
1. **Operations Page**: Detect format and handle both
   ```python
   def get_params_for_display(job_def):
       params_schema = job_def.params_schema or {}
       yaml_data = yaml.safe_load(job_def.yaml_content or "{}")
       ops_config = yaml_data.get("jobs", [{}])[0].get("ops_config", {})
       
       # Check if params_schema is prefixed (new format)
       has_prefixed = any('.' in key for key in params_schema.keys())
       
       if has_prefixed:
           # New format: Already prefixed
           return parse_prefixed_schema(params_schema, ops_config)
       elif ops_config:
           # Old format but has ops_config: Convert on-the-fly
           return convert_simple_to_prefixed(params_schema, ops_config)
       else:
           # Old format, no ops_config: Shared params only
           return parse_simple_schema(params_schema)
   ```

2. **Sync Process**: Auto-convert during sync
   ```python
   def sync_job_definitions(factory, all_configs):
       # ... existing sync logic ...
       
       # After storing job_def, check if conversion needed
       if job_def.params_schema and job_def.yaml_content:
           yaml_data = yaml.safe_load(job_def.yaml_content)
           ops_config = yaml_data.get("jobs", [{}])[0].get("ops_config", {})
           
           if ops_config:
               # Check if already prefixed
               has_prefixed = any('.' in key for key in job_def.params_schema.keys())
               if not has_prefixed:
                   # Convert simple → prefixed
                   job_def.params_schema = convert_to_prefixed(
                       job_def.params_schema, 
                       ops_config
                   )
   ```

**Conclusion**: ⚠️ **Needs backward compatibility** - But manageable.

---

### ✅ **Scenario 3: Shared vs Per-Asset Parameters**

**Static Job Example**:
```yaml
params_schema:
  target_bucket: "string!"      # Shared (all assets use same value)
  source_path: "string!"        # Shared (but can be overridden)
ops_config:
  phase2_cross_ref_asset_1:
    source_path: "/data/sales/input"  # Per-asset override
  phase2_cross_ref_asset_2:
    # No source_path → uses shared value from job_overrides
```

**After Change (Prefixed params_schema)**:
```yaml
params_schema:
  target_bucket: "string!"                           # Shared (no prefix)
  phase2_cross_ref_asset_1.source_path: "string!"   # Per-asset (prefixed)
  phase2_cross_ref_asset_2.source_path: "string!"   # Per-asset (prefixed)
ops_config:
  phase2_cross_ref_asset_1:
    source_path: "/data/sales/input"
```

**Logic for Conversion**:
```python
def convert_to_prefixed(simple_schema, ops_config):
    """Convert simple params_schema to prefixed format"""
    prefixed_schema = {}
    
    # Collect all params that appear in ops_config (per-asset params)
    per_asset_params = set()
    for asset_name, asset_params in ops_config.items():
        for param_name in asset_params.keys():
            per_asset_params.add(param_name)
            prefixed_key = f"{asset_name}.{param_name}"
            # Use existing type from simple_schema or default
            prefixed_schema[prefixed_key] = simple_schema.get(param_name, "string!")
    
    # Add shared params (not in ops_config)
    for param_name, param_type in simple_schema.items():
        if param_name not in per_asset_params:
            prefixed_schema[param_name] = param_type  # Keep simple name
    
    return prefixed_schema
```

**Conclusion**: ✅ **Works with hybrid approach** - Shared params stay simple, per-asset params get prefixed.

---

## Breaking Changes Assessment

### ❌ **What Would Break (Without Fixes)**

1. **Operations Page**: Can't display old static jobs (simple `params_schema`)
2. **Parameter Updates**: Can't update old static jobs (expects prefixed)
3. **Job Sync**: New static jobs with `ops_config` won't be converted

### ✅ **What Won't Break (With Fixes)**

1. **Static Asset Discovery**: Already prefixes for UI ✅
2. **Job Creation from Static Assets**: Will work with prefixed ✅
3. **Dagster Runtime**: Uses `ops_config` structure (unchanged) ✅
4. **Asset Definitions**: Use simple names `{{params.xxx}}` (unchanged) ✅

---

## Implementation Plan

### **Phase 1: Backward Compatibility (P0 - Critical)**

**File**: `pipelines.py` - `get_pipeline()` and `update_pipeline_params()`

```python
def get_pipeline(job_id, db):
    job_def = db.query(models.ETLJobDefinition).filter(...).first()
    
    # Normalize params_schema format
    params_schema = job_def.params_schema or {}
    yaml_data = yaml.safe_load(job_def.yaml_content or "{}")
    ops_config = extract_ops_config_from_yaml(yaml_data, job_def.job_nm)
    
    # Convert to prefixed if needed (for display)
    if ops_config and not is_prefixed_format(params_schema):
        params_schema = convert_to_prefixed(params_schema, ops_config)
    
    return schemas.Job(
        ...
        params_schema=params_schema,  # Always prefixed for display
        ops_config=ops_config
    )
```

### **Phase 2: Prefixed Storage for New Jobs (P1 - High)**

**File**: `graphs.py` - `create_job_definition()` and `update_job_definition()`

```python
def create_job_definition(request, db):
    # ... existing logic to build ops_config ...
    
    # Build prefixed params_schema
    prefixed_params_schema = {}
    
    # Add per-asset params (prefixed)
    for asset_name, asset_params in ops_config.items():
        for param_name in asset_params.keys():
            prefixed_key = f"{asset_name}.{param_name}"
            prefixed_params_schema[prefixed_key] = "string!"
    
    # Add shared params (simple names)
    for param_name in simple_params.keys():
        if param_name not in [p for ops in ops_config.values() for p in ops.keys()]:
            prefixed_params_schema[param_name] = "string!"
    
    # Store prefixed params_schema
    job_def.params_schema = prefixed_params_schema
    job_def.yaml_content = yaml_content  # Contains ops_config
```

### **Phase 3: Auto-Conversion During Sync (P2 - Medium)**

**File**: `sync_factory.py` - `sync_job_definitions()`

```python
def sync_job_definitions(factory, all_configs):
    # ... existing sync logic ...
    
    # After storing job_def
    if job_def.params_schema and job_def.yaml_content:
        yaml_data = yaml.safe_load(job_def.yaml_content)
        ops_config = extract_ops_config_from_yaml(yaml_data, job_def.job_nm)
        
        if ops_config:
            # Check if already prefixed
            if not is_prefixed_format(job_def.params_schema):
                # Convert simple → prefixed
                job_def.params_schema = convert_to_prefixed(
                    job_def.params_schema,
                    ops_config
                )
                # Update yaml_content to reflect new params_schema
                update_yaml_params_schema(job_def, job_def.params_schema)
                db.commit()
```

### **Phase 4: Migration Script (P3 - Low, Optional)**

**File**: `migrations/migrate_params_schema_to_prefixed.py`

```python
def migrate_static_jobs_to_prefixed(db):
    """One-time migration script for existing static jobs"""
    jobs = db.query(models.ETLJobDefinition).filter(
        models.ETLJobDefinition.params_schema.isnot(None),
        models.ETLJobDefinition.yaml_content.isnot(None)
    ).all()
    
    for job_def in jobs:
        yaml_data = yaml.safe_load(job_def.yaml_content)
        ops_config = extract_ops_config_from_yaml(yaml_data, job_def.job_nm)
        
        if ops_config and not is_prefixed_format(job_def.params_schema):
            job_def.params_schema = convert_to_prefixed(
                job_def.params_schema,
                ops_config
            )
            update_yaml_params_schema(job_def, job_def.params_schema)
    
    db.commit()
```

---

## Key Functions Needed

### **1. Format Detection**
```python
def is_prefixed_format(params_schema: dict) -> bool:
    """Check if params_schema uses prefixed format"""
    if not params_schema:
        return False
    return any('.' in key for key in params_schema.keys())
```

### **2. Conversion (Simple → Prefixed)**
```python
def convert_to_prefixed(simple_schema: dict, ops_config: dict) -> dict:
    """Convert simple params_schema to prefixed format"""
    prefixed_schema = {}
    
    # Collect per-asset params
    per_asset_params = set()
    for asset_name, asset_params in ops_config.items():
        for param_name in asset_params.keys():
            per_asset_params.add(param_name)
            prefixed_key = f"{asset_name}.{param_name}"
            prefixed_schema[prefixed_key] = simple_schema.get(param_name, "string!")
    
    # Add shared params (not in ops_config)
    for param_name, param_type in simple_schema.items():
        if param_name not in per_asset_params:
            prefixed_schema[param_name] = param_type
    
    return prefixed_schema
```

### **3. Ops Config Extraction**
```python
def extract_ops_config_from_yaml(yaml_data: dict, job_nm: str) -> dict:
    """Extract ops_config from YAML for a specific job"""
    jobs = yaml_data.get("jobs", [])
    for job in jobs:
        if job.get("name") == job_nm:
            return job.get("ops_config", {})
    return {}
```

---

## Testing Checklist

### ✅ **Test Cases**

1. **Static Asset Discovery**
   - [ ] Query `asset_metadata.params_schema` (simple names)
   - [ ] Return prefixed names for UI
   - [ ] Create job → Store prefixed in `params_schema`

2. **Static Job Display**
   - [ ] Old format (simple names) → Display correctly
   - [ ] New format (prefixed names) → Display correctly
   - [ ] Auto-convert old format if `ops_config` exists

3. **Parameter Updates**
   - [ ] Update prefixed param → Split to `ops_config`
   - [ ] Update shared param → Store in `parameter_values`
   - [ ] Update old format job → Convert to prefixed

4. **Job Creation**
   - [ ] Multi-asset job → Prefixed `params_schema`
   - [ ] Single-asset job → Simple `params_schema` (or prefixed?)
   - [ ] Shared params → Simple names in `params_schema`

5. **Job Sync**
   - [ ] Static job with `ops_config` → Auto-convert to prefixed
   - [ ] Static job without `ops_config` → Keep simple names
   - [ ] Blueprint sync → Handle appropriately

---

## Final Recommendation

### ✅ **YES, We Can Proceed** with these safeguards:

1. **Backward Compatibility**: Operations page handles both formats
2. **Auto-Conversion**: Sync process converts static jobs with `ops_config` to prefixed
3. **Hybrid Approach**: Shared params stay simple, per-asset params get prefixed
4. **Migration Path**: Optional script for existing static jobs

### **Critical Success Factors**:

1. ✅ Keep `asset_metadata.params_schema` as simple names (per-asset metadata)
2. ✅ Convert `etl_job_definition.params_schema` to prefixed for multi-asset jobs
3. ✅ Maintain backward compatibility for existing static jobs
4. ✅ Auto-convert during sync (not just on creation)

---

## Conclusion

**The proposed change will NOT break static files** if we:
- ✅ Implement backward compatibility in Operations Page
- ✅ Auto-convert static jobs with `ops_config` to prefixed format
- ✅ Keep `asset_metadata.params_schema` as simple names (per-asset metadata)
- ✅ Handle both formats gracefully in all parameter-related endpoints

**The key insight**: `params_schema` is UI metadata. Dagster runtime uses `ops_config` structure, which remains unchanged. We can safely change `params_schema` format as long as we handle backward compatibility.
