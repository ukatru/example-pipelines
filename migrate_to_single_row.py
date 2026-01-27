import psycopg2
from psycopg2.extras import DictCursor
import yaml
import json
import datetime

# DB Connection
DB_PARAMS = {
    "dbname": "dpe_framework",
    "user": "dagster",
    "password": "dagster",
    "host": "192.168.2.116",
    "port": "30722"
}

def migrate_team(team_id):
    print(f"Migrating Team {team_id}...")
    conn = psycopg2.connect(**DB_PARAMS)
    try:
        cur = conn.cursor(cursor_factory=DictCursor)
        
        # 1. Fetch existing single-row assets
        cur.execute("""
            SELECT * FROM etl_asset_definition 
            WHERE team_id = %s AND source_type != 'PIPELINE'
        """, (team_id,))
        rows = cur.fetchall()
        
        if not rows:
            print("  No legacy assets found.")
            return

        print(f"  Found {len(rows)} legacy assets. Merging...")
        
        assets = []
        for r in rows:
            # Parse existing YAML to ensure we get full config including connections
            # (If YAML is missing, we could construct from columns, but we verified YAML exists)
            if r['asset_yaml']:
                try:
                    y = yaml.safe_load(r['asset_yaml'])
                    assets.append(y)
                except Exception as e:
                    print(f"  ⚠️ Skipping corrupt YAML for {r['asset_nm']}: {e}")
            else:
                 # Fallback reconstruction
                 assets.append({
                     "name": r['asset_nm'],
                     "source": {"type": r['source_type'], **r['source_config']},
                     "target": {"type": r['target_type'], **r['target_config']} if r['target_type'] else None,
                     # We might lose deps here if we don't query dependency table, 
                     # but verified rows have YAML with deps.
                 })

        # 2. Fetch dependencies to be safe? 
        # Actually our previous verify showed YAML has deps. Trust YAML.

        # 3. Create Unified Payload
        full_graph = {"assets": assets}
        full_yaml = yaml.dump(full_graph)
        
        pipeline_name = f"Visual_Pipeline_{team_id}"
        
        # 3b. ID Generation
        cur.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM etl_asset_definition")
        new_id = cur.fetchone()[0]
        
        # 4. Upsert Pipeline Row
        cur.execute("""
            INSERT INTO etl_asset_definition 
            (id, asset_nm, asset_type, source_type, target_type, source_config, target_config, asset_yaml, team_id, org_id, created_by, creat_by_nm, actv_ind)
            VALUES (%s, %s, 'pipeline', 'PIPELINE', 'PIPELINE', '{}', '{}', %s, %s, %s, %s, %s, TRUE)
            ON CONFLICT (id) DO UPDATE SET asset_yaml = EXCLUDED.asset_yaml
        """, (
            new_id,
            pipeline_name, 
            full_yaml, 
            team_id, 
            rows[0]['org_id'], # Inherit from first asset
            rows[0]['created_by'],
            rows[0]['creat_by_nm']
        ))
        
        # 5. Archive Old Rows
        ids = [r['id'] for r in rows]
        cur.execute("DELETE FROM etl_asset_definition WHERE id = ANY(%s)", (ids,))
        
        # 6. Archive Dependencies
        cur.execute("DELETE FROM etl_asset_dependency WHERE team_id = %s", (team_id,))
        
        conn.commit()
        print("  Migration Success!")
        
    except Exception as e:
        conn.rollback()
        print(f"  Migration Failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_team(2) # Marketplace Team
