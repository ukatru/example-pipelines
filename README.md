# Example Pipelines Suite

This repository contains a comprehensive set of example pipelines used for validating the `dagster-dag-factory` framework. It serves as both a verification suite and a reference for building declarative DAGs.

## Standardized Project Structure

We follow a clean, root-based layout to simplify discovery and management of pipeline definitions:

```text
example-pipelines/
├── connections/         # Resource and connection definitions (YAML)
├── vars/               # Environment-specific configuration variables
├── pipelines/          # Unified Pipelines Directory
│   ├── sftp/, s3/, ... # YAML tech-specific subfolders
│   ├── __init__.py     # Package marker for Python imports
│   └── custom_assets.py # Native Python assets for power developers
├── definitions.py      # Main Entry Point (Merges YAML + Python)
└── pyproject.toml      # Dagster configurations
```

## Developer Roles

### Analyst (YAML-First)
Analysts can focus on the technology subfolders within the root `pipelines/` directory. By creating YAML files here, the framework automatically generates assets, jobs, and sensors.

### Power Developer (Python-First)
Engineers can extend the framework by writing native Dagster code directly in the `pipelines/` package (e.g., `custom_assets.py`).

## Adding New Pipelines

1.  **Define Connections**: Add any required resources to `connections/common.yaml` or environment-specific files.
2.  **Create Pipeline YAML**: Add your pipeline definition to the appropriate subfolder in `pipelines/`.
3.  **Automatic Discovery**: The `DagsterFactory` in `definitions.py` will automatically scan the recursive `pipelines/` directory and build the corresponding Dagster definitions.

## Validation

To verify the structural integrity of this project, you can run the validation script from the `dagster-dag-factory` root:

```bash
docker-compose exec dagster python verify_example_pipelines.py
```
