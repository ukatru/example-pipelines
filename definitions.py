from pathlib import Path
from dagster import Definitions
from nexus_foundry.dagster import DagsterFactory

# Import native Python definitions for power developers
from pipelines.custom_assets import python_processing_asset

# Import test jobs for multi-asset testing
from pipelines.tests.test_multi_asset_job import test_jobs

# Path to the root of example-pipelines
BASE_DIR = Path(__file__).parent

# 1. Initialize the Nexus Foundry Dagster Factory
factory = DagsterFactory(BASE_DIR)

# 2. Merge YAML-driven and Native definitions
defs = Definitions.merge(
    factory.build_definitions(),
    Definitions(
        assets=[python_processing_asset],
        jobs=test_jobs,  # Add test jobs for multi-asset testing
    )
)
