# Onboarding New Table: Their Approach vs Ours

## 🎯 Their Approach (Python Code + Tiny YAML)

### Step 1: Add Entry to YAML
```yaml
# defaults:.yaml
copy_jobs:
 - target_table: new_sales_table  # ← Just add this!
   source_file_url: "sales/(.+)\\.csv"
   description: "Load sales data"
   delimiter: ","
   has_headers: True
   dependencies: [move_actl_files_processed_inbound]
```

**That's it!** One entry, ~8 lines.

### Step 2: Python Code Handles Everything Else

**Assets**: Created in Python code (not shown, but `self.all_assets` is passed in)
**Connections**: Hardcoded (S3, Snowflake from EnvVars)
**Jobs**: Created in Python (`asset_job` with `selection=self.all_assets`)
**Source/Target**: Hardcoded (S3→Snowflake)

### How It Works:

1. **Preprocessor** reads YAML `copy_jobs`
2. **Maps** `target_table` → `asset_key` (line 60)
3. **Sensor** discovers files matching `source_file_url`
4. **Creates** `RunRequest` with:
   - `asset_selection`: `[AssetKey("new_sales_table")]`
   - `run_config`: `{"ops": {"new_sales_table": {"config": {...}}}}`

---

## 🎯 Our Approach (Full YAML)

### Step 1: Define Asset
```yaml
assets:
  - name: new_sales_table
    description: "Load sales data to Snowflake"
    group: sales
    source:
      type: S3
      connection: S3
      configs:
        bucket_name: "{{ params.source_bucket }}"
        key: "{{ params.file_pattern }}"
    target:
      type: SNOWFLAKE
      connection: SNOWFLAKE
      configs:
        table_name: "new_sales_table"
        stage: "{{ params.snowflake_stage }}"
        schema_strategy: "evolve"
    ins:
      upstream:
        key: move_actl_files_processed_inbound
```

### Step 2: Define Job
```yaml
jobs:
  - name: new_sales_table_job
    description: "Load new sales table"
    selection:
      - new_sales_table
    params_schema:
      source_bucket: "string!"
      file_pattern: "string!"
      snowflake_stage: "string!"
```

### Step 3: Define Sensor (if needed)
```yaml
sensors:
  - name: sales_file_sensor
    type: S3
    connection: S3
    configs:
      bucket_name: "{{ params.source_bucket }}"
      prefix: "sales"
      pattern: ".+\\.csv"
    job: new_sales_table_job
```

**Total**: ~40 lines per table.

---

## 📊 Comparison

| Aspect | Their Approach | Our Approach |
|--------|---------------|--------------|
| **Lines per Table** | ~8 lines | ~40 lines |
| **What's in YAML** | Just table config | Full asset definition |
| **Connections** | Hardcoded in code | Defined in YAML/DB |
| **Flexibility** | Fixed (S3→Snowflake) | Any source/target |
| **Onboarding Speed** | ⚡ Very fast | 🐢 Slower |
| **Maintenance** | Code changes needed | YAML only |

---

## ✅ Is Our Approach Easy for Onboarding?

### **Yes, but different:**

**Their Approach**:
- ✅ Fast: 1 entry in YAML
- ❌ Limited: Only S3→Snowflake
- ❌ Code changes: Need Python code for new patterns

**Our Approach**:
- ⚠️ More lines: Full asset definition
- ✅ Flexible: Any source/target
- ✅ No code: Everything in YAML

### **For Our Framework:**

**Onboarding is easy IF:**
1. You use **blueprints/templates** for common patterns
2. You **copy/paste** similar assets
3. You use **UI** to create assets (visual builder)

**Example Blueprint Approach**:
```yaml
# Blueprint: s3_to_snowflake_template
blueprint: true
assets:
  - name: "{{ table_name }}"  # Placeholder
    source:
      type: S3
      connection: S3
      configs:
        bucket_name: "{{ source_bucket }}"
        key: "{{ file_pattern }}"
    target:
      type: SNOWFLAKE
      connection: SNOWFLAKE
      configs:
        table_name: "{{ table_name }}"
        stage: "{{ stage }}"
```

**Then instantiate**:
```yaml
# Instantiate blueprint
table_name: new_sales_table
source_bucket: my-bucket
file_pattern: "sales/*.csv"
stage: my_stage
```

**Result**: Similar simplicity to their approach!

---

## 🎯 Key Takeaway

**Their YAML is small because:**
- Assets created in **Python code** (not YAML)
- Connections **hardcoded** (EnvVars)
- Pattern **fixed** (S3→Snowflake only)
- YAML = **configuration only**

**Our YAML is bigger because:**
- Assets **defined in YAML** (full definition)
- Connections **configurable** (flexible)
- Pattern **flexible** (any source/target)
- YAML = **complete specification**

**Both approaches are valid!**
- Theirs: Perfect for their specific use case
- Ours: Better for generic framework

**Best Solution**: Support both!
- Blueprints for common patterns (like theirs)
- Full definitions for flexibility (like ours)
