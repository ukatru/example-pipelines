from pathlib import Path
from dagster import Definitions
from metadata_framework import ParamsDagsterFactory

# Import native Python definitions for power developers
from pipelines.custom_assets import python_processing_asset

# Path to the root of example-pipelines
BASE_DIR = Path(__file__).parent

# 1. Initialize the Params-Aware Factory
# This location will default to enabling observability sensors unless 
# NEXUS_OBSERVABILITY_ENABLED=FALSE is set in the environment.
factory = ParamsDagsterFactory(BASE_DIR)

# 2. Merge YAML-driven and Native definitions into a single entry point
# We use Definitions.merge but ensure only 'defs' is at the module scope
defs = Definitions.merge(
    factory.build_definitions(),
    Definitions(
        assets=[python_processing_asset],
    )
)
