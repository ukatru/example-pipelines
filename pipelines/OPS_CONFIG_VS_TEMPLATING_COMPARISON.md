# Ops Config vs Templating: Comparison

## Current Approach (Templating) vs Ops Config (Python-style)

### Current YAML (Templating Approach)

```yaml
assets:
  - name: process_and_split_file
    source:
      configs:
        bucket_name: "{{ source.trigger.data.bucket_name }}"
        key: "{{ source.trigger.data.key }}"
    target:
      configs:
        bucket_name: "{{ params.aws_s3_bucket }}"
        prefix: "{{ params.processing_zone_prefix }}/{{ params.inbound_zone_prefix }}/{{ source.trigger.data.object_path.split('/')[0] }}"
        split_config:
          head_line_number: "{{ params.head_line_number }}"

jobs:
  - name: file_processor_job
    params_schema:
      aws_s3_bucket: "string|my-dagster-poc"
      head_line_number: "int"
    # No ops_config - uses templating
```

**How it works:**
- Sensor passes file data via `source.trigger.data.*`
- Assets use templating `{{ params.xxx }}` and `{{ source.trigger.data.xxx }}`
- Framework renders templates at runtime
- All config in asset definitions

---

### Ops Config Approach (Python-style)

```yaml
assets:
  - name: process_and_split_file
    source:
      configs:
        bucket_name: "{{ ops.process_and_split_file.config.source_bucket_name }}"
        key: "{{ ops.process_and_split_file.config.file_key }}"
    target:
      configs:
        bucket_name: "{{ ops.process_and_split_file.config.target_bucket_name }}"
        prefix: "{{ ops.process_and_split_file.config.target_prefix }}"
        split_config:
          head_line_number: "{{ ops.process_and_split_file.config.head_line_number }}"

jobs:
  - name: file_processor_job
    params_schema:
      aws_s3_bucket: "string|my-dagster-poc"
    ops_config:
      process_and_split_file:
        file_key: ""  # Sensor sets dynamically
        timestamp: ""  # Sensor sets dynamically
        source_bucket_name: ""  # Sensor sets dynamically
        target_bucket_name: "{{ params.aws_s3_bucket }}"
        head_line_number: 5
```

**How it works:**
- Sensor injects file-specific values into `ops_config` at runtime
- Assets access via `{{ ops.asset_name.config.field_name }}`
- Per-asset configuration in `ops_config` block
- Matches Python: `run_config["ops"][asset_name]["config"]`

---

## Key Differences

| Aspect | Templating (Current) | Ops Config (Python) |
|--------|-------------------|-------------------|
| **Config Location** | Asset definitions | `ops_config` in job |
| **File-Specific Data** | `{{ source.trigger.data.* }}` | `ops.{asset}.config.*` |
| **Per-Asset Overrides** | Hard to do | Easy (separate config per asset) |
| **Type Safety** | No (strings) | Yes (Pydantic if supported) |
| **Sensor Injection** | Via `source.trigger` | Via `ops_config` in run_config |
| **Python Match** | ❌ Different pattern | ✅ Matches exactly |

---

## Python Code Pattern

```python
# Python creates this structure:
run_config = {
    "ops": {
        "move_split_files_inbound_caller": {
            "config": {
                "file_key": "landing/file.csv",
                "timestamp": "20240101120000",
                "short_folder": "sales",
                "head_line_number": 5,
                # ... MoveFileConfig fields
            }
        },
        "execute_asset_job": {
            "config": {
                "asset_names": ["asset1", "asset2"],
                "file_key": "landing/file.csv",
                "file_key_surfix": "20240101120000"
            }
        }
    }
}
```

**Ops Config YAML matches this structure:**
```yaml
ops_config:
  process_and_split_file:
    file_key: ""  # Sensor sets
    timestamp: ""  # Sensor sets
    short_folder: ""  # Sensor sets
    head_line_number: 5
```

---

## Which Approach to Use?

### Use **Templating** (Current) when:
- ✅ Simple workflows
- ✅ Most params are shared
- ✅ File-specific data via `source.trigger.data.*` is sufficient
- ✅ Want config in asset definitions (more declarative)

### Use **Ops Config** when:
- ✅ Complex workflows with per-asset overrides
- ✅ Need to match Python code pattern exactly
- ✅ Want type-safe config (with Pydantic support)
- ✅ Sensor-driven workflows with dynamic config
- ✅ Multi-tenant or highly variable configs

---

## Framework Support

**Current Framework:**
- ✅ Supports templating (`{{ params.xxx }}`, `{{ source.trigger.data.xxx }}`)
- ✅ Supports `ops_config` in YAML (stored in DB)
- ⚠️ Assets access via templating (not direct ops config injection)
- ⚠️ Sensor would need to inject into `ops_config` (not yet implemented)

**To Fully Support Ops Config:**
1. Sensor factory needs to inject file data into `ops_config` in run_config
2. Asset factory needs to read from `ops.{asset_name}.config` (not just templating)
3. Framework needs to support both patterns (hybrid)
