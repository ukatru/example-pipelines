import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

# Absolute paths to repos
CORE_SRC = Path("/home/ukatru/github/nexus-core/src")
NEXUS_SRC = Path("/home/ukatru/github/nexus-foundry/src")
DDF_SRC = Path("/home/ukatru/github/dagster-dag-factory/src")
EXAMPLE_REPOS = Path("/home/ukatru/github/example-pipelines")

sys.path.insert(0, str(CORE_SRC))
sys.path.insert(0, str(NEXUS_SRC))
sys.path.insert(0, str(DDF_SRC))
sys.path.insert(0, str(EXAMPLE_REPOS))

from nexus_foundry.dagster import DagsterFactory

def test_hydration_cases():
    print("🚀 End-to-End Hydration Verification (example-pipelines)")
    
    # 1. Initialize Factory
    factory = DagsterFactory(base_dir=EXAMPLE_REPOS)
    print(f"📦 Factory initialized for team: {factory.team_nm}")
    
    asset_factory = factory.asset_factory
    
    # --- Case 1: Scheduled/Job Run (Explicit Job Name) ---
    print("\n--- CASE 1: Scheduled Job Run ---")
    mock_context_job = MagicMock()
    mock_context_job.job_name = "cross_ref_test_job"
    mock_context_job.run.tags = {
        "platform/type": "static",
        "job_nm": "cross_ref_test_job",
        "team": "Marketplace"
    }
    mock_context_job.run.run_config = {}
    mock_context_job.log.info = print
    
    tv_job = asset_factory._get_template_vars(mock_context_job)
    params_job = tv_job.get("params", {})
    
    assert params_job.get("source_path") == "/home/ukatru/data", f"Job hydration failed: {params_job}"
    print("✅ Case 1 Passed: Job-level hydration successful.")

    # --- Case 2: Manual UI Materialization (Golden Link) ---
    print("\n--- CASE 2: Manual UI Materialization (__ASSET_JOB) ---")
    mock_context_ui = MagicMock()
    mock_context_ui.job_name = "__ASSET_JOB"
    # No job_nm tag in run tags, simulating Dagster UI behavior
    mock_context_ui.run.tags = {
        "dagster/from_ui": "true"
    }
    mock_context_ui.run.run_config = {}
    mock_context_ui.log.info = print
    
    # 🟢 Simulate the 'Golden' Asset Definition Tags
    mock_asset_def = MagicMock()
    mock_asset_def.keys = {MagicMock(to_user_string=lambda: "cross_ref_test_asset")}
    mock_asset_def.tags_by_key = {
        next(iter(mock_asset_def.keys)): {
            "job_nm": "cross_ref_test_job",
            "platform/type": "static",
            "team": "Marketplace"
        }
    }
    mock_context_ui.assets_def = mock_asset_def
    
    tv_ui = asset_factory._get_template_vars(mock_context_ui)
    params_ui = tv_ui.get("params", {})
    
    assert params_ui.get("source_path") == "/home/ukatru/data", f"UI hydration failed: {params_ui}"
    print("✅ Case 2 Passed: 'Golden' tag inheritance from asset definition successful.")
    
    # --- Case 3: Registry-First Resource Resolution ---
    print("\n--- CASE 3: Registry-First Resource Resolution ---")
    os.environ["NEXUS_DB_ENABLED"] = "TRUE"
    
    # Mocking the Registry (DB + Secrets)
    from nexus_core.core.provider import JobParamsProvider
    from nexus_core.core.secrets import AWSSecretProvider
    
    mock_db_conn = MagicMock()
    mock_cur = mock_db_conn.cursor.return_value.__enter__.return_value
    # Simulate etl_connection record with secret_arn
    mock_cur.fetchone.return_value = {"conn_nm": "s3_prod", "config_json": {"secret_arn": "arn:aws:secretsmanager:us-west-2:123:secret:s3_prod"}}
    
    # Patch AWSSecretProvider globally for runtime resolution
    real_get_secret = AWSSecretProvider.get_secret
    AWSSecretProvider.get_secret = MagicMock(return_value={
        "bucket_name": "hardened-bucket-from-registry",
        "region_name": "us-east-1",
        "aws_secret_access_key": "mock-secret-key"
    })

    # Patch JobParamsProvider to use mocks
    real_get_conn = JobParamsProvider._get_connection
    JobParamsProvider._get_connection = MagicMock(return_value=mock_db_conn)

    # Initialize a new factory with DB enabled
    db_factory = DagsterFactory(base_dir=EXAMPLE_REPOS)
    
    # 🔴 The Test: Try to load 's3_prod' 
    # Even if it exists in local connections/ (us-west-2), the Registry (us-east-1) should win.
    resources = db_factory.resource_factory.load_resources_from_config({
        "s3_prod": {
            "type": "S3Resource",
            "config": {"region_name": "local-fallback-region"}
        }
    })
    
    s3_res = resources.get("s3_prod")
    # 1. Verify UI Masking (Definition side)
    assert s3_res.aws_secret_access_key == "******", f"UI Leak: Secret is visible! {s3_res.aws_secret_access_key}"
    
    # 2. Verify Literal visibility (Definition side)
    assert s3_res.region_name == "us-east-1", f"Registry-First (Lite) failed: {s3_res.region_name}"
    
    # 3. Verify Runtime Re-hydration (Resolution side)
    real_secret = s3_res.resolve("aws_secret_access_key")
    assert real_secret == "mock-secret-key", f"Runtime resolution failed: {real_secret}"
    
    # We can also verify it's the correct type
    from nexus_foundry.dagster.resources.s3 import S3Resource
    assert isinstance(s3_res, S3Resource)
    
    print("✅ Case 3 Passed: Registry-First priority and unpacking successful.")
    
    # Restore
    JobParamsProvider._get_connection = real_get_conn
    AWSSecretProvider.get_secret = real_get_secret
    
    print("\n✨ ALL VERIFICATION CASES PASSED!")

if __name__ == "__main__":
    test_hydration_cases()
