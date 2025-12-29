from dagster import asset

@asset(group_name="native_python")
def python_processing_asset():
    """
    Example of a native Python asset that power developers can write.
    This lives in pipelines/ and is merged with the YAML definitions.
    """
    return {"status": "success", "processed_by": "python"}
