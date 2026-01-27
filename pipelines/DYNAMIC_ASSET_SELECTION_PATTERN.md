# Dynamic Asset Selection Pattern (Python Code Analysis)

## Pattern from `s3_snowflake_injestion_job.py`

### Key Characteristics:

1. **Assets ARE defined** (not pure ops)
2. **Assets are selected dynamically** based on discovered files
3. **Ops config** provides file-specific parameters
4. **Sensor determines** which assets to run per file

---

## Python Code Structure

```python
@sensor(job=s3_snowflake_injestion_job, ...)
def actl_bnd_assets_sensor(context):
    # 1. Discover files
    for file in files:
        file_key = obj["Key"]
        file_match = get_file_match(file_name, container_folder, patterns)
        
        # 2. Create RunRequest with dynamic asset selection
        RunRequest(
            run_key=f"{file_key}-{timestamp}",
            asset_selection=selected_assets(file_names),  # ← Dynamic!
            run_config={
                "ops": {
                    "move_actl_files_processed_inbound": {
                        "config": {
                            "file_key_to_process": file_key,  # ← File-specific
                        }
                    }
                }
            }
        )

def selected_assets(file_names):
    # Always include base asset + file-specific assets
    return [AssetKey("move_actl_files_processed_inbound")] + (
        [AssetKey([file_name]) for file_name in file_names]
        if isinstance(file_names, list)
        else [AssetKey(file_names)]
    )
```

---

## Pattern Breakdown

### 1. **Base Asset** (Always Included)
- `move_actl_files_processed_inbound`
- Handles file processing/movement
- Gets file-specific config via ops_config

### 2. **Dynamic Assets** (Selected Per File)
- Selected based on `get_file_match()` result
- Example: `sales_data`, `marketing_data`
- Determined by file name + container folder matching patterns

### 3. **Ops Config** (File-Specific)
- Each file gets its own `ops_config`
- Contains file-specific parameters (file_key, etc.)
- Passed via `run_config["ops"][asset_name]["config"]`

### 4. **Asset Selection** (Dynamic)
- Sensor determines which assets to run
- Base asset + matched assets
- Different per file

---

## Comparison with Previous Examples

| Aspect | File Processor | S3 Snowflake Ingestion |
|--------|---------------|------------------------|
| **Structure** | Ops-based | Asset-based |
| **Selection** | Fixed (all ops) | Dynamic (per file) |
| **Config** | Ops config | Ops config |
| **Pattern** | Sensor → Job → Ops | Sensor → Job → Assets (dynamic) |

---

## Framework Support

### Current Framework:
- ✅ Supports `asset_selection` in RunRequest
- ✅ Supports `ops_config` in run_config
- ⚠️ Sensor uses fixed job selection (not dynamic)
- ⚠️ Sensor doesn't inject file-specific ops_config

### What's Needed:

1. **Dynamic Asset Selection in Sensor**:
   ```python
   # Sensor needs to:
   - Discover files
   - Match files to asset names (pattern matching)
   - Create RunRequest with dynamic asset_selection
   ```

2. **File-Specific Ops Config Injection**:
   ```python
   # Sensor needs to inject:
   run_config = {
       "ops": {
           "asset_name": {
               "config": {
                   "file_key": discovered_file_key,
                   # ... file-specific params
               }
           }
       }
   }
   ```

3. **Pattern Matching Support**:
   - Framework needs `get_file_match` equivalent
   - Maps: file_name + container_folder → asset names

---

## YAML Representation

See `s3_snowflake_ingestion_ops_config.yaml` for full example.

**Key Points**:
- Assets are defined statically
- Sensor dynamically selects which assets to run
- Ops config provides file-specific parameters
- Matches Python pattern exactly
