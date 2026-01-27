# 1:1 Graph Jobs Analysis: Same Graph, Multiple Assets

## Understanding "1:1 Graph Jobs"

**Definition**: A job that selects multiple assets from the **same graph** (same YAML file).

**Key Insight**: Parameters from the same graph typically **won't collide** because:
- They're designed together in the same file
- Shared parameters are intentionally shared
- Different assets use different parameter names or share intentionally

**Example**:
```yaml
# ui_test_graph_a.yaml (one graph)
assets:
  - name: sales_ingestion_asset
    source:
      configs:
        bucket_name: "{{ params.source_bucket }}"
        prefix: "{{ params.source_path }}"
  - name: sales_transformed_asset
    source:
      configs:
        bucket_name: "{{ params.target_bucket }}"  # Different param name
```

**Job Selection**: `["sales_ingestion_asset", "sales_transformed_asset"]` (both from same graph)

---

## Current Logic vs. Proposed Logic

### **Current Logic** (`inspect_selection_params` line 1850):
```python
should_prefix = len(all_asset_names) > 1
```

**Problem**: This prefixes **all** multi-asset jobs, even when they're from the same graph (no collision risk).

**Result**:
- Same graph, 2 assets → Prefixed: `["sales_ingestion_asset.source_bucket", "sales_transformed_asset.target_bucket"]`
- Different graphs, 2 assets → Prefixed: `["sales_ingestion_asset.source_bucket", "marketing_ingestion_asset.source_bucket"]`

**Issue**: Unnecessary prefixing for same-graph jobs!

---

### **Proposed Logic: Smart Prefixing**

**Rule**: Only prefix when assets come from **different graphs** (collision risk).

```python
# Determine if assets are from same graph or different graphs
asset_graphs = {}
for asset in assets:
    # Get graph_id or file_loc for each asset
    graph_id = asset.graph_id if hasattr(asset, 'graph_id') else None
    file_loc = get_file_loc_for_asset(asset)  # For static assets
    asset_graphs[asset.asset_nm] = (graph_id, file_loc)

# Check if all assets are from same graph
unique_graphs = set(asset_graphs.values())
is_same_graph = len(unique_graphs) == 1

# Only prefix if multiple assets AND from different graphs
should_prefix = len(all_asset_names) > 1 and not is_same_graph
```

**Result**:
- Same graph, 2 assets → Simple: `["source_bucket", "target_bucket"]` ✅
- Different graphs, 2 assets → Prefixed: `["sales_ingestion_asset.source_bucket", "marketing_ingestion_asset.source_bucket"]` ✅
- Single asset → Simple: `["source_bucket"]` ✅

---

## Implementation Strategy

### **1. Track Graph/File Source for Each Asset**

**For UI-Created Assets** (`ETLAssetDefinition`):
```python
# Assets from same graph have same graph_id
graph_id = asset.graph_id
```

**For Static Assets** (`AssetMetadata`):
```python
# Assets from same file have same file_loc
file_loc = asset.file_loc
```

### **2. Group Assets by Source**

```python
def group_assets_by_source(assets, static_assets):
    """Group assets by their graph/file source"""
    source_map = {}
    
    # UI-created assets (by graph_id)
    for asset in assets:
        source_key = f"graph:{asset.graph_id}" if asset.graph_id else "orphan"
        if source_key not in source_map:
            source_map[source_key] = []
        source_map[source_key].append(asset.asset_nm)
    
    # Static assets (by file_loc)
    for asset in static_assets:
        source_key = f"file:{asset.file_loc}" if asset.file_loc else "orphan"
        if source_key not in source_map:
            source_map[source_key] = []
        source_map[source_key].append(asset.asset_name)
    
    return source_map
```

### **3. Determine Prefixing Strategy**

```python
def should_prefix_params(assets, static_assets):
    """Determine if parameters should be prefixed"""
    if len(assets) + len(static_assets) <= 1:
        return False  # Single asset, no prefix needed
    
    # Group by source
    source_map = group_assets_by_source(assets, static_assets)
    
    # If all assets from same source, no prefix needed
    if len(source_map) == 1:
        return False  # Same graph/file, no collision risk
    
    # Multiple sources, prefix needed
    return True  # Different graphs/files, collision risk
```

---

## Updated Flow

### **Discovery Phase** (`inspect_selection_params`)

```python
# Collect all assets (UI-created + static)
all_assets = list(assets) + list(static_assets)

# Determine if prefixing needed
should_prefix = should_prefix_params(assets, static_assets)

# In add_schema_to_map:
def add_schema_to_map(schema_dict, source_nm):
    # ... existing logic ...
    
    if should_prefix:
        prefixed_name = f"{source_nm}.{p_name}"
    else:
        prefixed_name = p_name  # Simple name, no prefix
```

### **Job Creation Phase** (`create_job_definition`)

```python
# Check if job is from same graph
asset_selection = request.asset_selection
selected_assets = resolve_assets_from_selection(asset_selection)

# Determine if all assets from same graph
is_same_graph = all_assets_from_same_source(selected_assets)

if is_same_graph:
    # Same graph: Use simple params_schema (no prefix)
    params_schema = build_simple_params_schema(selected_assets)
    # No ops_config needed (shared params)
else:
    # Different graphs: Use prefixed params_schema
    params_schema = build_prefixed_params_schema(selected_assets, ops_config)
    # ops_config needed for per-asset overrides
```

---

## Benefits

### ✅ **1. Cleaner UI for Same-Graph Jobs**

**Before** (unnecessary prefixing):
```
Parameters:
  - sales_ingestion_asset.source_bucket
  - sales_ingestion_asset.source_path
  - sales_transformed_asset.target_bucket
```

**After** (simple names):
```
Parameters:
  - source_bucket
  - source_path
  - target_bucket
```

### ✅ **2. Simpler Parameter Configuration**

**Same Graph**: User configures shared parameters once (no per-asset confusion)
**Different Graphs**: User sees prefixed names (clear which asset each param belongs to)

### ✅ **3. Consistent with Static Jobs**

**Static Job** (from same file):
```yaml
jobs:
  - name: phase2_cross_ref_static_job
    params_schema:
      source_path: "string!"      # Simple names (same file)
      target_bucket: "string!"
    ops_config:
      phase2_cross_ref_asset_1:
        source_path: "/data/sales/input"  # Per-asset override
```

**UI-Created Job** (from same graph):
- Should also use simple names in `params_schema`
- Only use `ops_config` if user wants per-asset overrides

---

## Edge Cases

### **Case 1: Mixed Sources (Some from Graph, Some Static)**

**Scenario**: User selects:
- `sales_ingestion_asset` (from graph `sales_pipeline`)
- `marketing_ingestion_asset` (from static file `ui_test_graph_b.yaml`)

**Decision**: **Prefix needed** (different sources, collision risk)

### **Case 2: Same Graph, But User Wants Per-Asset Overrides**

**Scenario**: User selects 2 assets from same graph, but wants different `source_bucket` values.

**Decision**: 
- `params_schema`: Simple names (shared params)
- `ops_config`: Per-asset overrides (if user configures them)

**Example**:
```yaml
params_schema:
  source_bucket: "string!"  # Simple name (shared)
ops_config:
  sales_ingestion_asset:
    source_bucket: "sales-bucket"  # Override for this asset
  sales_transformed_asset:
    source_bucket: "transformed-bucket"  # Override for this asset
```

### **Case 3: Same File, Different Assets (Static)**

**Scenario**: User selects 2 assets from same static file.

**Decision**: **No prefix needed** (same file, designed together)

---

## Implementation Changes

### **File**: `graphs.py` - `inspect_selection_params`

```python
def should_prefix_params(assets, static_assets):
    """Determine if parameters should be prefixed based on asset sources"""
    total_assets = len(assets) + len(static_assets)
    
    if total_assets <= 1:
        return False  # Single asset, no prefix
    
    # Group by source
    sources = set()
    
    # UI-created assets: group by graph_id
    for asset in assets:
        source = f"graph:{asset.graph_id}" if asset.graph_id else "orphan"
        sources.add(source)
    
    # Static assets: group by file_loc
    for asset in static_assets:
        source = f"file:{asset.file_loc}" if asset.file_loc else "orphan"
        sources.add(source)
    
    # If all from same source, no prefix needed
    return len(sources) > 1  # Multiple sources = prefix needed

# In inspect_selection_params:
should_prefix = should_prefix_params(assets, static_assets)

# In add_schema_to_map:
if should_prefix:
    prefixed_name = f"{source_nm}.{p_name}"
else:
    prefixed_name = p_name  # Simple name
```

### **File**: `graphs.py` - `create_job_definition`

```python
# Determine if all assets from same source
def all_assets_from_same_source(asset_selection, db):
    """Check if all selected assets are from the same graph/file"""
    # Resolve assets from selection
    assets = resolve_assets_from_selection(asset_selection, db)
    static_assets = resolve_static_assets_from_selection(asset_selection, db)
    
    # Group by source
    sources = set()
    for asset in assets:
        sources.add(f"graph:{asset.graph_id}" if asset.graph_id else "orphan")
    for asset in static_assets:
        sources.add(f"file:{asset.file_loc}" if asset.file_loc else "orphan")
    
    return len(sources) == 1

# In create_job_definition:
is_same_source = all_assets_from_same_source(request.asset_selection, db)

if is_same_source:
    # Same graph/file: Simple params_schema
    params_schema = build_simple_params_schema(simple_params, ops_config)
else:
    # Different sources: Prefixed params_schema
    params_schema = build_prefixed_params_schema(simple_params, ops_config)
```

---

## Summary

### **Key Decision**: Only prefix when assets come from **different graphs/files**

**Logic**:
- ✅ **Same graph/file, multiple assets**: Simple names (no prefix)
- ✅ **Different graphs/files, multiple assets**: Prefixed names (collision risk)
- ✅ **Single asset**: Simple names (no prefix)

**Benefits**:
- Cleaner UI for same-graph jobs
- Simpler parameter configuration
- Consistent with static jobs
- Only prefix when actually needed (collision risk)

**Implementation**:
- Track asset source (graph_id or file_loc)
- Group assets by source
- Only prefix if multiple sources detected

---

## Conclusion

**Answer**: For 1:1 graph jobs (same graph, multiple assets), we should **NOT prefix** parameters because:
1. Parameters are designed together (no collision risk)
2. Simpler UI (no unnecessary prefixes)
3. Consistent with static jobs from same file
4. Only prefix when actually needed (different graphs/files)

This makes the system smarter: **prefix only when there's actual collision risk**, not just because there are multiple assets.
