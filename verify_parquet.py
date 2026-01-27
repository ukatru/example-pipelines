#!/usr/bin/env python3
"""
Parquet File Verification Script
Verifies the Parquet file produced by the S3-to-S3 operator
"""

import pandas as pd
import pyarrow.parquet as pq
import os
import sys

parquet_file = 'AdventureWorksSales_All.parquet'
csv_file = 'AdventureWorksSales_All.csv'

def verify_parquet():
    print("=" * 70)
    print("FULL PARQUET FILE VERIFICATION".center(70))
    print("=" * 70)
    
    if not os.path.exists(parquet_file):
        print(f"❌ ERROR: {parquet_file} not found!")
        return False
    
    if not os.path.exists(csv_file):
        print(f"⚠️  WARNING: {csv_file} not found - skipping comparison")
        csv_df = None
    else:
        csv_df = pd.read_csv(csv_file, low_memory=False)
    
    # Read Parquet file using pyarrow directly
    try:
        parquet_table = pq.read_table(parquet_file)
        parquet_df = parquet_table.to_pandas()
        print(f"✅ Parquet file read successfully using pyarrow")
    except Exception as e:
        print(f"❌ ERROR reading Parquet file: {e}")
        return False
    
    if csv_df is None:
        # Just verify Parquet structure
        print(f"\n1. Parquet File Statistics:")
        print(f"   Rows: {len(parquet_df):,}")
        print(f"   Columns: {len(parquet_df.columns):,}")
        print(f"   ✅ Parquet file is valid and readable")
        return True
    
    print(f"\n1. Data Statistics:")
    print(f"   CSV rows: {len(csv_df):,}")
    print(f"   Parquet rows: {len(parquet_df):,}")
    row_match = len(csv_df) == len(parquet_df)
    print(f"   Row count match: {'✅ YES' if row_match else '❌ NO'}")
    
    print(f"   CSV columns: {len(csv_df.columns):,}")
    print(f"   Parquet columns: {len(parquet_df.columns):,}")
    col_count_match = len(csv_df.columns) == len(parquet_df.columns)
    print(f"   Column count match: {'✅ YES' if col_count_match else '❌ NO'}")
    
    csv_cols = set(csv_df.columns)
    parquet_cols = set(parquet_df.columns)
    col_name_match = csv_cols == parquet_cols
    print(f"   Column names match: {'✅ YES' if col_name_match else '❌ NO'}")
    
    if not col_name_match:
        csv_only = csv_cols - parquet_cols
        parquet_only = parquet_cols - csv_cols
        if csv_only:
            print(f"   CSV only ({len(csv_only)}): {list(csv_only)[:5]}")
        if parquet_only:
            print(f"   Parquet only ({len(parquet_only)}): {list(parquet_only)[:5]}")
    
    print(f"\n2. Sample Data Check:")
    # Compare first row
    csv_first = csv_df.iloc[0]
    parquet_first = parquet_df.iloc[0]
    
    sample_cols = list(csv_df.columns[:5])
    first_row_matches = 0
    for col in sample_cols:
        csv_val = csv_first[col]
        parquet_val = parquet_first[col]
        csv_str = str(csv_val) if not pd.isna(csv_val) else "None"
        parquet_str = str(parquet_val) if not pd.isna(parquet_val) else "None"
        if csv_str == parquet_str:
            first_row_matches += 1
    
    print(f"   First row matches (first 5 cols): {first_row_matches}/5 {'✅' if first_row_matches == 5 else '⚠️'}")
    
    # Compare last row
    csv_last = csv_df.iloc[-1]
    parquet_last = parquet_df.iloc[-1]
    
    last_row_matches = 0
    for col in sample_cols:
        csv_val = csv_last[col]
        parquet_val = parquet_last[col]
        csv_str = str(csv_val) if not pd.isna(csv_val) else "None"
        parquet_str = str(parquet_val) if not pd.isna(parquet_val) else "None"
        if csv_str == parquet_str:
            last_row_matches += 1
    
    print(f"   Last row matches (first 5 cols): {last_row_matches}/5 {'✅' if last_row_matches == 5 else '⚠️'}")
    
    # Show sample comparison
    print(f"\n   Sample comparison (first column):")
    first_col = csv_df.columns[0]
    csv_val = csv_first[first_col]
    parquet_val = parquet_first[first_col]
    print(f"   CSV[{first_col}]: {csv_val}")
    print(f"   Parquet[{first_col}]: {parquet_val}")
    print(f"   Match: {'✅' if str(csv_val) == str(parquet_val) else '❌'}")
    
    # Check SalesOrderNumber if available
    sales_match = False
    if 'SalesOrderNumber' in csv_df.columns and 'SalesOrderNumber' in parquet_df.columns:
        print(f"\n3. Key Column Check (SalesOrderNumber):")
        csv_sales = set(csv_df['SalesOrderNumber'].dropna().astype(str))
        parquet_sales = set(parquet_df['SalesOrderNumber'].dropna().astype(str))
        print(f"   Unique values in CSV: {len(csv_sales):,}")
        print(f"   Unique values in Parquet: {len(parquet_sales):,}")
        sales_match = csv_sales == parquet_sales
        print(f"   SalesOrderNumber values match: {'✅ YES' if sales_match else '❌ NO'}")
        
        if not sales_match:
            diff = csv_sales - parquet_sales
            if diff:
                print(f"   Missing in Parquet: {len(diff)} values")
            diff2 = parquet_sales - csv_sales
            if diff2:
                print(f"   Extra in Parquet: {len(diff2)} values")
    
    # Check data types
    print(f"\n4. Data Type Information (first 5 columns):")
    print(f"   CSV dtypes:")
    for col in csv_df.columns[:5]:
        print(f"      {col:30s}: {csv_df[col].dtype}")
    print(f"   Parquet dtypes:")
    for col in parquet_df.columns[:5]:
        print(f"      {col:30s}: {parquet_df[col].dtype}")
    
    # Check for NULL handling
    print(f"\n5. NULL Value Handling:")
    csv_nulls = csv_df.isnull().sum().sum()
    parquet_nulls = parquet_df.isnull().sum().sum()
    print(f"   Total NULL values in CSV: {csv_nulls:,}")
    print(f"   Total NULL values in Parquet: {parquet_nulls:,}")
    null_match = csv_nulls == parquet_nulls
    print(f"   NULL count match: {'✅ YES' if null_match else '⚠️  CHECK' if abs(csv_nulls - parquet_nulls) < 100 else '❌ NO'}")
    
    # Check compression info
    print(f"\n6. Parquet File Properties:")
    parquet_file_obj = pq.ParquetFile(parquet_file)
    metadata = parquet_file_obj.metadata
    print(f"   Row groups: {metadata.num_row_groups}")
    if metadata.num_row_groups > 0:
        compression = metadata.row_group(0).column(0).compression
        print(f"   Compression: {compression}")
    
    # File size comparison
    csv_size = os.path.getsize(csv_file)
    parquet_size = os.path.getsize(parquet_file)
    compression_ratio = (1 - parquet_size / csv_size) * 100
    print(f"\n7. File Size Comparison:")
    print(f"   CSV size: {csv_size:,} bytes ({csv_size / 1024 / 1024:.2f} MB)")
    print(f"   Parquet size: {parquet_size:,} bytes ({parquet_size / 1024 / 1024:.2f} MB)")
    print(f"   Compression: {compression_ratio:.1f}% smaller")
    
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY".center(70))
    print("=" * 70)
    all_checks = []
    if row_match:
        all_checks.append("✅ Row count matches CSV")
    if col_count_match:
        all_checks.append("✅ Column count matches CSV")
    if col_name_match:
        all_checks.append("✅ Column names match CSV")
    if first_row_matches == 5:
        all_checks.append("✅ First row data matches")
    if last_row_matches == 5:
        all_checks.append("✅ Last row data matches")
    if 'SalesOrderNumber' in csv_df.columns:
        if sales_match:
            all_checks.append("✅ Key column (SalesOrderNumber) values match")
    
    for check in all_checks:
        print(check)
    
    if row_match and col_count_match and col_name_match and first_row_matches == 5 and last_row_matches == 5:
        if 'SalesOrderNumber' in csv_df.columns and sales_match:
            print("\n✅✅✅ CONVERSION SUCCESSFUL - All checks passed! ✅✅✅")
            return True
        else:
            print("\n✅✅✅ CONVERSION SUCCESSFUL - Core checks passed! ✅✅✅")
            return True
    else:
        print("\n⚠️  Some mismatches detected - see details above")
        return False
    print("=" * 70)

if __name__ == "__main__":
    success = verify_parquet()
    sys.exit(0 if success else 1)
