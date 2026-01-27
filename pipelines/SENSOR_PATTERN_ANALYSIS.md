# Sensor Pattern Analysis: One Sensor vs Multiple Sensors

## 🎯 Your Question

> "In their case one sensor monitors all the file patterns or they create one sensor per source_file_url?"

---

## 🔍 Answer: **ONE Sensor Monitors ALL Patterns**

Looking at `Preprocessor.py`:

### **Their Pattern: One Sensor, Multiple Patterns**

```python
def create_s3_preprocessor_assets_sensor(self, name="s3_preprocessor_assets_sensor"):
    @dg.sensor(
        name=name,
        job=combined_preprocessor_asset_materialization,
        minimum_interval_seconds=sensor_interval_override,
        default_status=dg.DefaultSensorStatus.RUNNING,
        required_resource_keys={"s3", "snowflake"},
    )
    def s3_preprocessor_assets_sensor(context: dg.SensorEvaluationContext):
        # 1. List ALL objects in landing zone
        all_objects = self.list_s3_objects_sorted(context, self.landing_zone_prefix)
        
        # 2. Loop through ALL folders
        for file in all_objects:
            obj_key = file["Key"]
            # ... process folders ...
        
        # 3. For each file, check against ALL copy_jobs
        for file in files_in_folder:
            obj_key = file["Key"]
            
            # Loop through ALL file_processors (each has a source_file_regex)
            for fp in list(
                filter(
                    lambda fp: fp.copy_job["short_folder"] == short_folder,
                    self.file_processors,  # ← ALL file processors
                )
            ):
                # Match file against THIS file_processor's pattern
                if re.match(
                    clean_up_url(fp.copy_job["source_file_regex"]),  # ← Pattern from copy_job
                    clean_up_url(obj_key, self.landing_zone_prefix),
                ):
                    # Create RunRequest for this matching pattern
                    # ...
```

**Key Points:**
1. **One sensor** (`s3_preprocessor_assets_sensor`)
2. **Monitors one prefix** (`landing_zone_prefix`)
3. **Checks all files** against **all patterns** from `copy_jobs`
4. **Creates RunRequest** for each matching pattern

---

## 📊 How It Works

### **Step 1: Sensor Lists All Files**
```python
all_objects = self.list_s3_objects_sorted(context, self.landing_zone_prefix)
# Returns: ["landing/folder1/file1.csv", "landing/folder2/file2.csv", ...]
```

### **Step 2: For Each File, Check All Patterns**
```python
for file in files_in_folder:
    obj_key = file["Key"]  # e.g., "landing/bnd/file.csv"
    
    # Check against ALL file_processors
    for fp in self.file_processors:
        # Each fp has: fp.copy_job["source_file_regex"]
        # e.g., "bnd/(data_)BndAnalytics_(.+)(\\d{8})(__.+)\.txt"
        
        if re.match(fp.copy_job["source_file_regex"], obj_key):
            # Match found! Create RunRequest for this asset
            # asset_key = fp.copy_job["asset_key"]  # e.g., "poc_analytics"
```

### **Step 3: One File Can Match Multiple Patterns**
```python
# File: "landing/bnd/BndAnalytics_20240101__header.txt"
# 
# Pattern 1: "bnd/(data_)BndAnalytics_(.+)(\\d{8})(__.+)\.txt" → Matches!
#   → Asset: "poc_analytics"
#
# Pattern 2: "bnd/(data_)BndAnalytics_(.+)(\\d{8})(__.+)\.txt" → Matches!
#   → Asset: "header_poc_analytics"
#
# Result: Multiple RunRequests (one per matching pattern)
```

---

## 🆚 Comparison: One Sensor vs Multiple Sensors

### **Their Approach: One Sensor, All Patterns**

```python
# ONE sensor
@sensor(name="s3_preprocessor_assets_sensor")
def sensor(context):
    # List all files
    all_files = list_s3_objects("landing")
    
    # Check each file against ALL patterns
    for file in all_files:
        for pattern in all_patterns:  # ← All copy_jobs patterns
            if matches(file, pattern):
                create_run_request(asset_for_pattern)
```

**Pros:**
- ✅ **Simple**: One sensor definition
- ✅ **Efficient**: One S3 list call
- ✅ **Centralized**: All logic in one place
- ✅ **Flexible**: Easy to add new patterns (just add to `copy_jobs`)

**Cons:**
- ❌ **Complex Logic**: Sensor needs to handle all patterns
- ❌ **Single Point of Failure**: If sensor breaks, all patterns stop

---

### **Alternative: Multiple Sensors, One Pattern Each**

```python
# MULTIPLE sensors (one per pattern)
@sensor(name="sensor_poc_analytics")
def sensor_poc_analytics(context):
    files = list_s3_objects("landing", pattern="poc_analytics_pattern")
    for file in files:
        create_run_request("poc_analytics")

@sensor(name="sensor_header_poc_analytics")
def sensor_header_poc_analytics(context):
    files = list_s3_objects("landing", pattern="header_pattern")
    for file in files:
        create_run_request("header_poc_analytics")
```

**Pros:**
- ✅ **Simple Logic**: Each sensor handles one pattern
- ✅ **Isolated**: One sensor failure doesn't affect others
- ✅ **Parallel**: Sensors can run independently

**Cons:**
- ❌ **More Sensors**: One sensor per pattern
- ❌ **More S3 Calls**: Each sensor lists S3 separately
- ❌ **More Code**: Need to create sensor per pattern

---

## 🎯 Why They Use One Sensor

### **1. All Patterns Share Same Landing Zone**
```yaml
copy_jobs:
 - target_table: poc_analytics
   source_file_url: "processed/inbound/bnd/pattern1"
 - target_table: header_poc_analytics
   source_file_url: "processed/inbound/bnd/pattern2"
```
**Same prefix**: `landing_zone_prefix` = `"landing"`
**One sensor** can monitor all patterns in same location.

### **2. Patterns Are Related (Same Group)**
```yaml
group: poc_bnd

copy_jobs:
 - target_table: poc_analytics
 - target_table: header_poc_analytics
```
**Same group**: All assets in `poc_bnd` group
**One sensor** handles all assets in the group.

### **3. Efficient: One S3 List Call**
```python
all_objects = self.list_s3_objects_sorted(context, self.landing_zone_prefix)
# One call gets all files, then filter by pattern
```
**More efficient** than multiple sensors each listing S3 separately.

---

## 🔄 How Our Framework Handles This

### **Current Framework: One Sensor Per YAML Definition**

```yaml
sensors:
  - name: s3_preprocessor_sensor
    type: S3
    configs:
      bucket_name: "my-bucket"
      prefix: "landing"
      pattern: ".*\\.csv"  # ← Single pattern
    job: file_processor_job
```

**Current Behavior:**
- One sensor per YAML definition
- Each sensor has one `pattern`
- Sensor triggers job for matching files

### **To Match Their Pattern: Multiple Patterns in One Sensor**

**Option 1: Multiple Sensors (Current)**
```yaml
sensors:
  - name: sensor_poc_analytics
    type: S3
    configs:
      prefix: "landing"
      pattern: "poc_analytics_pattern"
    job: file_processor_job
  
  - name: sensor_header_poc_analytics
    type: S3
    configs:
      prefix: "landing"
      pattern: "header_pattern"
    job: file_processor_job
```

**Option 2: One Sensor, Multiple Patterns (Like Theirs)**
```yaml
sensors:
  - name: s3_preprocessor_sensor
    type: S3
    configs:
      prefix: "landing"
      patterns:  # ← Multiple patterns
        - "poc_analytics_pattern"
        - "header_pattern"
    job: file_processor_job
    # Sensor logic matches file against all patterns
    # Creates RunRequest per matching pattern
```

**Option 3: Sensor with Pattern Matching Logic**
```yaml
sensors:
  - name: s3_preprocessor_sensor
    type: S3
    configs:
      prefix: "landing"
      pattern: ".*"  # ← Match all files
    job: file_processor_job
    # Sensor logic:
    # 1. List all files in prefix
    # 2. For each file, check against all asset patterns
    # 3. Create RunRequest for matching assets
```

---

## 📝 Summary

### **Their Approach:**
- ✅ **ONE sensor** monitors **ALL patterns**
- ✅ Sensor lists all files in landing zone
- ✅ For each file, checks against all `copy_jobs` patterns
- ✅ Creates RunRequest for each matching pattern

### **Why It Works:**
- All patterns share same landing zone
- Patterns are related (same group)
- Efficient: One S3 list call
- Simple: One sensor definition

### **Our Framework:**
- Currently: **One sensor per YAML definition**
- Each sensor has one `pattern`
- Can create multiple sensors for multiple patterns

### **To Match Their Pattern:**
- **Option 1**: Keep current (multiple sensors)
- **Option 2**: Support multiple patterns in one sensor
- **Option 3**: Sensor with pattern matching logic (like theirs)

**Recommendation**: Current approach (multiple sensors) is fine for most cases. If needed, we can add support for multiple patterns in one sensor later.
