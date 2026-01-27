# Restartability Analysis: Their Sensor Pattern

## 🎯 Your Observation

> "I think they lose restartability if it fails while looping through many files if one file fails right?"

**You're absolutely right!** There's a critical issue with their cursor management.

---

## 🔍 The Problem

### **Their Code (Preprocessor.py lines 174-254):**

```python
for file in files_in_folder:
    obj_key = file["Key"]
    
    for fp in self.file_processors:
        if re.match(fp.copy_job["source_file_regex"], obj_key):
            # ... create RunRequest config ...
            
            run_key = f"{obj_key}__{file['LastModified'].isoformat()}"
            
            context.update_cursor(run_key)  # ← CURSOR UPDATED HERE (line 248)
            
            yield dg.RunRequest(              # ← RUNREQUEST YIELDED HERE (line 252)
                run_key=run_key, 
                run_config=run_config
            )
```

### **The Issue:**

**Cursor is updated BEFORE RunRequest is yielded!**

**Problem Scenarios:**

#### **Scenario 1: Sensor Crashes After Cursor Update**
```python
# File 1: Processed successfully
context.update_cursor(run_key_1)  # ← Cursor updated
yield RunRequest(...)              # ← RunRequest yielded ✅

# File 2: Cursor updated, but sensor crashes before yield
context.update_cursor(run_key_2)  # ← Cursor updated ✅
# Sensor crashes here! ❌
# yield RunRequest(...)            # ← Never executed!
```

**Result:**
- Cursor is updated for file 2
- RunRequest was never yielded
- On restart, sensor skips file 2 (cursor already updated)
- **File 2 is lost!** ❌

#### **Scenario 2: Exception During Loop**
```python
# Files 1-4: Processed successfully
for i in range(1, 5):
    context.update_cursor(run_key_i)  # ← Cursor updated
    yield RunRequest(...)              # ← RunRequest yielded ✅

# File 5: Exception occurs
context.update_cursor(run_key_5)  # ← Cursor updated ✅
raise Exception("Something broke!")  # ← Sensor crashes ❌
# yield RunRequest(...)            # ← Never executed!
```

**Result:**
- Cursor updated for files 1-5
- RunRequests yielded for files 1-4 only
- On restart, sensor skips files 1-5 (cursor already updated)
- **File 5 is lost!** ❌

#### **Scenario 3: Partial Processing**
```python
# Process 10 files
for file in files[1:10]:
    context.update_cursor(run_key)  # ← Cursor updated for each
    yield RunRequest(...)            # ← RunRequest yielded
    
# Sensor crashes after file 5
# Files 6-10: Cursor not updated, RunRequests not yielded
```

**Result:**
- Files 1-5: Cursor updated, RunRequests yielded ✅
- Files 6-10: Cursor not updated, RunRequests not yielded
- On restart:
  - Files 1-5: Skipped (cursor already updated) ✅
  - Files 6-10: Reprocessed (cursor not updated) ✅
- **This case works, but only if crash happens AFTER yield**

---

## 🆚 Our Framework's Approach

### **Our Code (sensor_factory.py lines 100-139):**

```python
if found_items:
    for item in found_items:
        # ... create RunRequest ...
        yield RunRequest(...)  # ← YIELD FIRST
    
    # IMPORTANT: Update cursor state ONLY AFTER constructing trigger metadata
    # to prevent potential state bleed in the current tick loop.
    if new_cursor:
        context.update_cursor(new_cursor)  # ← CURSOR UPDATED AFTER ALL YIELDS
```

### **Why Our Approach is Better:**

1. **All RunRequests yielded first** ✅
2. **Cursor updated only after all yields succeed** ✅
3. **If sensor crashes, cursor not updated** ✅
4. **On restart, all files reprocessed** ✅

**Trade-off:**
- If sensor crashes after yields but before cursor update, files are reprocessed (idempotent operations handle this)
- Better than losing files!

---

## 🔧 The Correct Pattern

### **Option 1: Update Cursor After All Yields (Our Approach)**

```python
run_requests = []
for file in files:
    if matches(file, pattern):
        run_requests.append(create_run_request(file))

# Yield all RunRequests first
for run_request in run_requests:
    yield run_request

# Update cursor only after all yields succeed
if run_requests:
    context.update_cursor(max_mtime)
```

**Pros:**
- ✅ No lost files
- ✅ Safe restartability
- ✅ Files reprocessed if sensor crashes

**Cons:**
- ❌ Files might be reprocessed (but idempotent ops handle this)

---

### **Option 2: Update Cursor Per File, But After Yield**

```python
for file in files:
    if matches(file, pattern):
        run_request = create_run_request(file)
        yield run_request  # ← Yield first
        
        # Update cursor only after successful yield
        context.update_cursor(file['mtime'])
```

**Pros:**
- ✅ Cursor updated per file
- ✅ No lost files (cursor updated after yield)

**Cons:**
- ❌ More cursor updates (less efficient)
- ❌ Still risky if yield fails after cursor update

---

### **Option 3: Use RunRequest's run_key as Cursor (Their Attempt)**

```python
run_key = f"{obj_key}__{file['LastModified'].isoformat()}"
context.update_cursor(run_key)  # ← Using run_key as cursor
yield RunRequest(run_key=run_key, ...)
```

**Problem:**
- Cursor updated before yield ❌
- If yield fails, cursor already updated ❌
- File is lost on restart ❌

**Their Issue:**
- They're using `run_key` as cursor, but updating it BEFORE yield
- Should update AFTER yield, or use a different cursor strategy

---

## 📊 Comparison

| Aspect | Their Approach | Our Approach |
|--------|---------------|--------------|
| **Cursor Update** | Before yield ❌ | After all yields ✅ |
| **Lost Files** | Possible ❌ | No ✅ |
| **Restartability** | Risky ❌ | Safe ✅ |
| **Reprocessing** | Avoids (but loses files) | Allows (idempotent) |
| **Efficiency** | More cursor updates | Fewer cursor updates |

---

## 🎯 Recommendations

### **For Their Code:**

**Fix: Update cursor AFTER yield**
```python
for file in files:
    if matches(file, pattern):
        run_key = f"{obj_key}__{file['LastModified'].isoformat()}"
        
        yield dg.RunRequest(  # ← Yield first
            run_key=run_key, 
            run_config=run_config
        )
        
        context.update_cursor(run_key)  # ← Update after yield
```

**Or: Update cursor after all yields**
```python
run_requests = []
for file in files:
    if matches(file, pattern):
        run_requests.append(create_run_request(file))

# Yield all first
for run_request in run_requests:
    yield run_request

# Update cursor after all yields
if run_requests:
    max_mtime = max(file['LastModified'] for file in processed_files)
    context.update_cursor(str(max_mtime))
```

### **For Our Framework:**

**Current approach is correct!** ✅
- Update cursor after all yields
- Safe restartability
- No lost files

---

## 📝 Summary

**Your Observation: ✅ Correct!**

**Their Issue:**
- Cursor updated BEFORE yield
- If sensor crashes, cursor already updated
- File is lost on restart ❌

**Our Approach:**
- Cursor updated AFTER all yields
- If sensor crashes, cursor not updated
- Files reprocessed on restart ✅
- No lost files ✅

**Key Principle:**
> **Always update cursor AFTER successful operations, not before!**
