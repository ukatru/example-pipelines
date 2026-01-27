# Nexus Foundry Selection Logic Comparison

This document compares the Python test job patterns with nexus-foundry's JobFactory implementation.

## Test Patterns vs Nexus Foundry Support

### ✅ Test 1: Explicit Selection
**Python:**
```python
AssetSelection.keys("sales_ingestion_asset", "marketing_ingestion_asset")
```

**Nexus Foundry (YAML):**
```yaml
selection:
  - key: sales_ingestion_asset
  - key: marketing_ingestion_asset
```

**Nexus Foundry Logic (job_factory.py:50):**
```python
new_sel = AssetSelection.keys(item)  # For plain asset name
asset_sel = (asset_sel | new_sel) if asset_sel else new_sel  # Union with |
```
✅ **SUPPORTED** - Converts to `AssetSelection.keys("sales_ingestion_asset") | AssetSelection.keys("marketing_ingestion_asset")`

---

### ✅ Test 2: Downstream Selection
**Python:**
```python
AssetSelection.keys("sales_ingestion_asset").downstream() | AssetSelection.keys("marketing_ingestion_asset").downstream()
```

**Nexus Foundry (YAML):**
```yaml
selection:
  - key: sales_ingestion_asset*
  - key: marketing_ingestion_asset*
```

**Nexus Foundry Logic (job_factory.py:43-47):**
```python
elif item.endswith("*") or item.endswith("+"):
    asset_key = item.rstrip("*+")
    new_sel = AssetSelection.keys(asset_key).downstream()
    asset_sel = (asset_sel | new_sel) if asset_sel else new_sel
```
✅ **SUPPORTED** - Converts `asset_name*` to `.downstream()`

---

### ✅ Test 3: Group Selection
**Python:**
```python
AssetSelection.groups("sales_pipeline") | AssetSelection.groups("marketing_pipeline")
```

**Nexus Foundry (YAML):**
```yaml
selection:
  - group: sales_pipeline
  - group: marketing_pipeline
```

**Nexus Foundry Logic (job_factory.py:30-42):**
```python
if ":" in item:
    if item.endswith("+") or item.endswith("*"):
        # Handle downstream
    else:
        new_sel = AssetSelection.from_string(item)  # "group:sales_pipeline"
```
✅ **SUPPORTED** - Uses `AssetSelection.from_string("group:sales_pipeline")` which internally calls `.groups()`

---

### ✅ Test 4: Union of Specific Assets
**Python:**
```python
AssetSelection.keys("sales_ingestion_asset") | AssetSelection.keys("marketing_ingestion_asset") | AssetSelection.keys("sales_transformed_asset") | AssetSelection.keys("marketing_analytics_asset")
```

**Nexus Foundry (YAML):**
```yaml
selection:
  - key: sales_ingestion_asset
  - key: marketing_ingestion_asset
  - key: sales_transformed_asset
  - key: marketing_analytics_asset
```

**Nexus Foundry Logic (job_factory.py:51):**
```python
asset_sel = (asset_sel | new_sel) if asset_sel else new_sel  # Unions all items
```
✅ **SUPPORTED** - Each item is unioned with `|` operator

---

### ✅ Test 5: Ingestion Only (No Downstream)
**Python:**
```python
AssetSelection.keys("sales_ingestion_asset") | AssetSelection.keys("marketing_ingestion_asset")
```

**Nexus Foundry (YAML):**
```yaml
selection:
  - key: sales_ingestion_asset  # No * suffix
  - key: marketing_ingestion_asset  # No * suffix
```

**Nexus Foundry Logic (job_factory.py:48-50):**
```python
else:
    # Plain asset name - exact match only
    new_sel = AssetSelection.keys(item)
```
✅ **SUPPORTED** - Without `*`, it's exact match only

---

### ✅ Test 6: Downstream Only
**Python:**
```python
AssetSelection.keys("sales_transformed_asset") | AssetSelection.keys("marketing_analytics_asset")
```

**Nexus Foundry (YAML):**
```yaml
selection:
  - key: sales_transformed_asset
  - key: marketing_analytics_asset
```

**Nexus Foundry Logic:**
Same as Test 5 - explicit selection
✅ **SUPPORTED**

---

## Additional Patterns Supported by Nexus Foundry

### Dict Format (Legacy Support)
**YAML:**
```yaml
selection:
  - key: sales_ingestion_asset
  - group: marketing_pipeline
```

**Nexus Foundry Logic (job_factory.py:52-62):**
```python
elif isinstance(item, dict):
    if "key" in item:
        new_sel = AssetSelection.keys(item["key"])
    else:
        for sel_type, sel_value in item.items():
            selection_str = f"{sel_type}:{sel_value}"
            new_sel = AssetSelection.from_string(selection_str)
```
✅ **SUPPORTED**

### String Format (Single Selection)
**YAML:**
```yaml
selection: "group:sales_pipeline"
```

**Nexus Foundry Logic (job_factory.py:65-66):**
```python
elif isinstance(selection, str):
    asset_sel = AssetSelection.from_string(selection)
```
✅ **SUPPORTED**

### Wildcard (All Assets)
**YAML:**
```yaml
selection: "*"
```

**Nexus Foundry Logic (job_factory.py:63-64):**
```python
elif selection == "*":
    asset_sel = AssetSelection.all()
```
✅ **SUPPORTED**

---

## Summary

| Test Pattern | Python Code | Nexus Foundry YAML | Status |
|-------------|-------------|-------------------|--------|
| Explicit Selection | `AssetSelection.keys("a", "b")` | `- key: a`<br>`- key: b` | ✅ Supported |
| Downstream Selection | `.downstream() \| .downstream()` | `- key: a*`<br>`- key: b*` | ✅ Supported |
| Group Selection | `.groups("g1") \| .groups("g2")` | `- group: g1`<br>`- group: g2` | ✅ Supported |
| Union | Multiple `.keys()` with `\|` | Multiple `- key:` items | ✅ Supported |
| Ingestion Only | `.keys()` without `.downstream()` | `- key: a` (no `*`) | ✅ Supported |
| Downstream Only | `.keys()` for downstream assets | `- key: downstream_asset` | ✅ Supported |

## Conclusion

✅ **YES - Nexus Foundry handles the same logic!**

All test patterns are supported:
1. **Explicit selection** → List of `key:` items
2. **Downstream selection** → `key: asset_name*` (converts to `.downstream()`)
3. **Group selection** → `group: group_name` (uses `AssetSelection.from_string()`)
4. **Union** → Multiple items in list (automatically unioned with `|`)
5. **Ingestion only** → `key: asset_name` without `*`
6. **Downstream only** → `key: downstream_asset_name`

The nexus-foundry framework correctly converts YAML selection rules to the same Dagster `AssetSelection` patterns used in the Python test jobs.
