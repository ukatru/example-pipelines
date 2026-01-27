import sys
import os

# Add nexus-foundry to path BEFORE installed packages
sys.path.insert(0, "/home/ukatru/github/nexus-foundry/src")
sys.path.insert(0, "/home/ukatru/github/nexus-core/src")

from nexus_foundry.dagster.factory.dagster_factory import DagsterFactory
print(f"DEBUG: Loaded DagsterFactory from: {DagsterFactory.__module__}")
import nexus_foundry.dagster.factory.dagster_factory
print(f"DEBUG: File: {nexus_foundry.dagster.factory.dagster_factory.__file__}")

from nexus_core.core.provider import JobParamsProvider

def verify():
    # Set Env Vars for Connection
    os.environ["DB_NAME"] = "dpe_framework"
    os.environ["DB_USER"] = "dagster"
    os.environ["DB_PASSWORD"] = "dagster"
    os.environ["DB_HOST"] = "192.168.2.116"
    os.environ["DB_PORT"] = "30722"

    print("Initializing DagsterFactory...")
    factory = DagsterFactory(base_dir=os.getcwd())
    factory.team_id = 2 # Manually set team ID context
    
    print("Loading Custom Assets for Team 2...")
    assets = factory._load_custom_assets()
    
    print(f"\nFound {len(assets)} Asset Config Groups (Files).")
    for group in assets:
        print(f"File: {group['file']}")
        print(f"Folder: {group['folders']}")
        print(f"Is Dynamic: {group['is_dynamic']}")
        print(f"Num Assets inside: {len(group['config']['assets'])}")
        for a in group['config']['assets']:
             # Handle both nested 'source_config' or flattened structures
             src_type = a.get('source', {}).get('type')
             src_conn = a.get('source', {}).get('connection')
             print(f"  - Asset: {a.get('name')} | Source: {src_type} | Connection: {src_conn}")

if __name__ == "__main__":
    verify()
