import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Path setup
BASE_DIR = Path(__file__).parent.absolute()
NEXUS_FOUNDRY_SRC = Path("/home/ukatru/github/nexus-foundry/src")
NEXUS_CORE_SRC = Path("/home/ukatru/github/nexus-core/src")

sys.path.insert(0, str(NEXUS_FOUNDRY_SRC))
sys.path.insert(0, str(NEXUS_CORE_SRC))

load_dotenv(BASE_DIR / ".env")

from nexus_foundry.dagster import DagsterFactory
from nexus_core.core.provider import JobParamsProvider

def debug():
    factory = DagsterFactory(BASE_DIR)
    print(f"--- DagsterFactory Initialization ---")
    print(f"Team: {factory.team_nm} (ID: {factory.team_id})")
    print(f"Org: {factory.org_code} (ID: {factory.org_id})")
    print(f"Location: {factory.location_name} (ID: {factory.code_location_id})")
    print(f"DB Enabled: {factory.db_enabled}")
    
    print(f"\n--- Database Inspection ---")
    provider = JobParamsProvider(BASE_DIR)
    
    # 1. Check all teams
    with provider._get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, team_nm, org_id FROM etl_team")
            teams = cur.fetchall()
            print(f"Teams in DB: {teams}")
            
    # 2. Check assets for the resolved team_id
    assets = provider.get_custom_assets(team_id=factory.team_id)
    print(f"Assets found for Team ID {factory.team_id}: {len(assets)}")
    for a in assets:
        print(f"  - {a['asset_nm']} (ID: {a['id']}, Team ID: {a['team_id']})")

    # 3. Check assets for ALL teams (just in case of mismatch)
    with provider._get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, asset_nm, team_id FROM etl_asset_definition WHERE actv_ind = true")
            all_assets = cur.fetchall()
            print(f"\nAll Active Assets in DB: {all_assets}")

if __name__ == "__main__":
    debug()
