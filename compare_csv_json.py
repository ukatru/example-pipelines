#!/usr/bin/env python3
import csv
import json

# Read CSV (handle BOM)
csv_file = open('AdventureWorksSales_All.csv', encoding='utf-8-sig')
csv_rows = list(csv.DictReader(csv_file))
csv_file.close()

# Read JSON
with open('AdventureWorksSales_All.json', 'r') as f:
    json_data = json.load(f)

print("=" * 60)
print("CSV to JSON Conversion Validation")
print("=" * 60)

# 1. Row count comparison
print(f"\n1. Row Count:")
print(f"   CSV rows: {len(csv_rows):,}")
print(f"   JSON records: {len(json_data):,}")
print(f"   Match: {'✅ YES' if len(csv_rows) == len(json_data) else '❌ NO'}")

# 2. Column/Key comparison
csv_headers = set(csv_rows[0].keys())
json_keys = set(json_data[0].keys())
print(f"\n2. Column/Key Comparison:")
print(f"   CSV columns: {len(csv_headers)}")
print(f"   JSON keys: {len(json_keys)}")
print(f"   Match: {'✅ YES' if csv_headers == json_keys else '❌ NO'}")
if csv_headers != json_keys:
    csv_only = csv_headers - json_keys
    json_only = json_keys - csv_headers
    if csv_only:
        print(f"   CSV only: {csv_only}")
    if json_only:
        print(f"   JSON only: {json_only}")

# 3. Data integrity check (sample)
print(f"\n3. Data Integrity Check (first 10 rows):")
mismatches = []
for i in range(min(10, len(csv_rows))):
    if csv_rows[i] != json_data[i]:
        mismatches.append(i)
        if len(mismatches) == 1:  # Show first mismatch details
            csv_row = csv_rows[i]
            json_row = json_data[i]
            diff_keys = [k for k in csv_row.keys() if str(csv_row[k]) != str(json_row.get(k, ''))]
            print(f"   Row {i}: ❌ MISMATCH")
            print(f"      Different fields: {diff_keys[:5]}")
            if diff_keys:
                sample_key = diff_keys[0]
                print(f"      CSV[{sample_key}]: {csv_row[sample_key]}")
                print(f"      JSON[{sample_key}]: {json_row.get(sample_key)}")

if not mismatches:
    print(f"   ✅ All 10 rows match perfectly!")

# 4. First and last record validation
print(f"\n4. Boundary Records:")
print(f"   First record:")
print(f"      CSV SalesOrderNumber: {csv_rows[0]['SalesOrderNumber']}")
print(f"      JSON SalesOrderNumber: {json_data[0]['SalesOrderNumber']}")
print(f"      Match: {'✅' if csv_rows[0]['SalesOrderNumber'] == json_data[0]['SalesOrderNumber'] else '❌'}")
print(f"   Last record:")
print(f"      CSV SalesOrderNumber: {csv_rows[-1]['SalesOrderNumber']}")
print(f"      JSON SalesOrderNumber: {json_data[-1]['SalesOrderNumber']}")
print(f"      Match: {'✅' if csv_rows[-1]['SalesOrderNumber'] == json_data[-1]['SalesOrderNumber'] else '❌'}")

# 5. Sample data comparison
print(f"\n5. Sample Data (first record, first 5 fields):")
for i, key in enumerate(list(csv_rows[0].keys())[:5]):
    csv_val = csv_rows[0][key]
    json_val = json_data[0].get(key, 'MISSING')
    match = str(csv_val) == str(json_val)
    print(f"   {key}:")
    print(f"      CSV:  {csv_val}")
    print(f"      JSON: {json_val}")
    print(f"      Match: {'✅' if match else '❌'}")

# 6. Overall assessment
print(f"\n" + "=" * 60)
print("OVERALL ASSESSMENT:")
print("=" * 60)
all_good = (
    len(csv_rows) == len(json_data) and
    csv_headers == json_keys and
    len(mismatches) == 0
)
if all_good:
    print("✅ CONVERSION IS WORKING CORRECTLY!")
    print("   - All rows converted")
    print("   - All columns preserved")
    print("   - Data integrity maintained")
else:
    print("⚠️  CONVERSION HAS ISSUES:")
    if len(csv_rows) != len(json_data):
        print(f"   - Row count mismatch: {len(csv_rows)} vs {len(json_data)}")
    if csv_headers != json_keys:
        print(f"   - Column/key mismatch")
    if mismatches:
        print(f"   - Data mismatches found in sample rows")
