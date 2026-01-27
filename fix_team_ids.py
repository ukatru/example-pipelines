import psycopg2
import os
from pathlib import Path

def fix_team_ids():
    db_params = {
        "dbname": "dpe_framework",
        "user": "dagster",
        "password": "dagster",
        "host": "192.168.2.116",
        "port": "30722"
    }
    
    conn = psycopg2.connect(**db_params)
    try:
        with conn.cursor() as cur:
            # 1. Update Assets
            # SFTP_S3_STEP2 and SFTP_S3 were saved as team_id 1, fix to 2 (Marketplace)
            cur.execute("""
                UPDATE etl_asset_definition 
                SET team_id = 2 
                WHERE asset_nm IN ('SFTP_S3_STEP2', 'SFTP_S3') AND team_id = 1
            """)
            print(f"Updated {cur.rowcount} assets to Team ID 2")
            
            # 2. Update Dependencies
            cur.execute("""
                UPDATE etl_asset_dependency 
                SET team_id = 2 
                WHERE team_id = 1 AND asset_id IN (
                    SELECT id FROM etl_asset_definition WHERE team_id = 2
                )
            """)
            print(f"Updated {cur.rowcount} dependencies to Team ID 2")
            
            conn.commit()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_team_ids()
