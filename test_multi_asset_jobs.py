#!/usr/bin/env python3
"""
Test script to verify multi-asset job creation and selection
Tests all combinations of sales and marketing assets
"""
from definitions import defs
from dagster import AssetSelection

def test_job_selections():
    """Test various job selection patterns"""
    print("=" * 80)
    print("MULTI-ASSET JOB SELECTION TESTS")
    print("=" * 80)
    
    # Get all assets
    all_assets = defs.get_all_asset_defs()
    asset_keys = [asset.key.to_user_string() for asset in all_assets]
    
    print(f"\nAvailable Assets ({len(asset_keys)}):")
    for key in sorted(asset_keys):
        print(f"  - {key}")
    
    # Get all jobs
    all_jobs = defs.get_all_job_defs()
    print(f"\nAvailable Jobs ({len(all_jobs)}):")
    for job in all_jobs:
        print(f"  - {job.name}")
        if hasattr(job, 'asset_selection'):
            try:
                resolved = job.asset_selection.resolve(all_assets)
                print(f"    Resolves to {len(resolved)} assets")
            except:
                print(f"    Selection: {job.asset_selection}")
    
    # Test 1: Explicit selection
    print("\n" + "=" * 80)
    print("TEST 1: Explicit Selection")
    print("=" * 80)
    sel1 = AssetSelection.keys("sales_ingestion_asset", "marketing_ingestion_asset")
    selected1 = sel1.resolve(all_assets)
    print(f"Selection: sales_ingestion_asset, marketing_ingestion_asset")
    print(f"Resolved Assets ({len(selected1)}):")
    for asset in selected1:
        print(f"  - {asset.key.to_user_string()}")
    
    # Test 2: Downstream selection
    print("\n" + "=" * 80)
    print("TEST 2: Downstream Selection")
    print("=" * 80)
    sel2 = AssetSelection.keys("sales_ingestion_asset").downstream() | AssetSelection.keys("marketing_ingestion_asset").downstream()
    selected2 = sel2.resolve(all_assets)
    print(f"Selection: sales_ingestion_asset* | marketing_ingestion_asset*")
    print(f"Resolved Assets ({len(selected2)}):")
    for asset in selected2:
        print(f"  - {asset.key.to_user_string()}")
    
    # Test 3: Group selection
    print("\n" + "=" * 80)
    print("TEST 3: Group Selection")
    print("=" * 80)
    try:
        sel3 = AssetSelection.groups("sales_pipeline") | AssetSelection.groups("marketing_pipeline")
        selected3 = sel3.resolve(all_assets)
        print(f"Selection: group:sales_pipeline | group:marketing_pipeline")
        print(f"Resolved Assets ({len(selected3)}):")
        for asset in selected3:
            print(f"  - {asset.key.to_user_string()}")
    except Exception as e:
        print(f"Error: {e}")
        selected3 = []
    
    # Test 4: Union of specific assets
    print("\n" + "=" * 80)
    print("TEST 4: Union of Specific Assets")
    print("=" * 80)
    sel4 = (AssetSelection.keys("sales_ingestion_asset") 
            | AssetSelection.keys("marketing_ingestion_asset")
            | AssetSelection.keys("sales_transformed_asset")
            | AssetSelection.keys("marketing_analytics_asset"))
    selected4 = sel4.resolve(all_assets)
    print(f"Selection: All 4 assets explicitly")
    print(f"Resolved Assets ({len(selected4)}):")
    for asset in selected4:
        print(f"  - {asset.key.to_user_string()}")
    
    # Test 5: Check dependencies
    print("\n" + "=" * 80)
    print("TEST 5: Dependency Analysis")
    print("=" * 80)
    print("Sales Pipeline:")
    sales_ingestion = [a for a in all_assets if a.key.to_user_string() == "sales_ingestion_asset"]
    if sales_ingestion:
        asset = sales_ingestion[0]
        deps = [dep.to_user_string() for dep in asset.dependency_keys] if hasattr(asset, 'dependency_keys') else []
        print(f"  sales_ingestion_asset dependencies: {deps}")
        print(f"  sales_ingestion_asset has downstream: sales_transformed_asset")
    
    print("\nMarketing Pipeline:")
    marketing_ingestion = [a for a in all_assets if a.key.to_user_string() == "marketing_ingestion_asset"]
    if marketing_ingestion:
        asset = marketing_ingestion[0]
        deps = [dep.to_user_string() for dep in asset.dependency_keys] if hasattr(asset, 'dependency_keys') else []
        print(f"  marketing_ingestion_asset dependencies: {deps}")
        print(f"  marketing_ingestion_asset has downstream: marketing_analytics_asset")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total assets available: {len(asset_keys)}")
    print(f"Total jobs defined: {len(all_jobs)}")
    print("\nSelection Results:")
    print(f"  Test 1 (Explicit): {len(selected1)} assets")
    print(f"  Test 2 (Downstream): {len(selected2)} assets")
    print(f"  Test 3 (Groups): {len(selected3)} assets")
    print(f"  Test 4 (Union): {len(selected4)} assets")
    
    print("\n" + "=" * 80)
    print("KEY INSIGHTS")
    print("=" * 80)
    print("1. Explicit selection (Test 1): Only selects the exact assets specified")
    print("2. Downstream selection (Test 2): Selects assets + all their downstream dependencies")
    print("3. Group selection (Test 3): Selects all assets in the specified groups")
    print("4. Union (Test 4): Combines multiple selections using | operator")
    print("\nFor multi-asset jobs with per-asset config:")
    print("  - Use explicit selection or downstream selection")
    print("  - Parameters are discovered from all selected assets")
    print("  - ops_config maps parameters to specific assets")

if __name__ == "__main__":
    test_job_selections()
