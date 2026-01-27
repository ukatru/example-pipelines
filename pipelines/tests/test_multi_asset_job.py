"""
Test Multi-Asset Job Creation
Tests various combinations of selecting sales and marketing assets
"""
from dagster import define_asset_job, AssetSelection, Definitions
from pathlib import Path

# Test 1: Select both ingestion assets explicitly
test_job_1_explicit = define_asset_job(
    name="test_multi_asset_explicit",
    description="Test: Explicitly select sales_ingestion_asset and marketing_ingestion_asset",
    selection=AssetSelection.keys("sales_ingestion_asset", "marketing_ingestion_asset"),
    tags={"test": "explicit_selection", "domain": "multi_asset"}
)

# Test 2: Select with downstream (using * syntax equivalent)
test_job_2_downstream = define_asset_job(
    name="test_multi_asset_downstream",
    description="Test: Select sales_ingestion_asset and marketing_ingestion_asset with downstream",
    selection=AssetSelection.keys("sales_ingestion_asset").downstream() 
            | AssetSelection.keys("marketing_ingestion_asset").downstream(),
    tags={"test": "downstream_selection", "domain": "multi_asset"}
)

# Test 3: Select by groups
test_job_3_groups = define_asset_job(
    name="test_multi_asset_groups",
    description="Test: Select by groups (sales_pipeline and marketing_pipeline)",
    selection=AssetSelection.groups("sales_pipeline") | AssetSelection.groups("marketing_pipeline"),
    tags={"test": "group_selection", "domain": "multi_asset"}
)

# Test 4: Select specific assets with union
test_job_4_union = define_asset_job(
    name="test_multi_asset_union",
    description="Test: Union of specific assets",
    selection=AssetSelection.keys("sales_ingestion_asset") 
            | AssetSelection.keys("marketing_ingestion_asset")
            | AssetSelection.keys("sales_transformed_asset")
            | AssetSelection.keys("marketing_analytics_asset"),
    tags={"test": "union_selection", "domain": "multi_asset"}
)

# Test 5: Select ingestion assets only (no downstream)
test_job_5_ingestion_only = define_asset_job(
    name="test_multi_asset_ingestion_only",
    description="Test: Only ingestion assets (no downstream)",
    selection=AssetSelection.keys("sales_ingestion_asset") 
            | AssetSelection.keys("marketing_ingestion_asset"),
    tags={"test": "ingestion_only", "domain": "multi_asset"}
)

# Test 6: Select downstream assets only
test_job_6_downstream_only = define_asset_job(
    name="test_multi_asset_downstream_only",
    description="Test: Only downstream assets (transformed/analytics)",
    selection=AssetSelection.keys("sales_transformed_asset") 
            | AssetSelection.keys("marketing_analytics_asset"),
    tags={"test": "downstream_only", "domain": "multi_asset"}
)

# Export all test jobs
test_jobs = [
    test_job_1_explicit,
    test_job_2_downstream,
    test_job_3_groups,
    test_job_4_union,
    test_job_5_ingestion_only,
    test_job_6_downstream_only,
]
