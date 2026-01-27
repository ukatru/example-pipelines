#!/usr/bin/env python3
"""
Quick script to verify if static assets from ui_test_graph_a.yaml and ui_test_graph_b.yaml
are synced to the asset_metadata table.
"""
import os
import sys
from pathlib import Path

# Add parent directory to path to import nexus modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "nexus-foundry" / "src"))

try:
    from nexus_core.core.provider import JobParamsProvider
    
    # Get base dir (example-pipelines)
    base_dir = Path(__file__).parent.parent.parent
    provider = JobParamsProvider(base_dir)
    conn = provider._get_connection()
    
    try:
        with conn.cursor() as cur:
            # Check for our test assets
            test_assets = [
                'sales_ingestion_asset',
                'sales_transformed_asset',
                'marketing_ingestion_asset',
                'marketing_analytics_asset'
            ]
            
            print("=" * 60)
            print("Checking for test assets in asset_metadata table...")
            print("=" * 60)
            
            cur.execute("""
                SELECT 
                    asset_key,
                    asset_name,
                    group_name,
                    team_nm,
                    graph_id,
                    asset_definition_id,
                    partition_type,
                    actv_ind,
                    creat_dttm,
                    updt_dttm
                FROM asset_metadata
                WHERE asset_key = ANY(%s)
                ORDER BY asset_key
            """, (test_assets,))
            
            results = cur.fetchall()
            
            if results:
                print(f"\n✅ Found {len(results)} test assets:\n")
                for row in results:
                    asset_key, asset_name, group_name, team_nm, graph_id, asset_def_id, partition_type, actv_ind, creat_dttm, updt_dttm = row
                    print(f"  Asset: {asset_key}")
                    print(f"    Name: {asset_name}")
                    print(f"    Group: {group_name}")
                    print(f"    Team: {team_nm}")
                    print(f"    graph_id: {graph_id} (should be NULL for static)")
                    print(f"    asset_definition_id: {asset_def_id} (should be NULL for static)")
                    print(f"    Partition Type: {partition_type}")
                    print(f"    Active: {actv_ind}")
                    print(f"    Created: {creat_dttm}")
                    print(f"    Updated: {updt_dttm}")
                    print()
            else:
                print("\n❌ No test assets found in asset_metadata table!")
                print("\nThis could mean:")
                print("  1. Sync hasn't run yet (restart Dagster/reload code location)")
                print("  2. NEXUS_SYNC_ENABLED is False")
                print("  3. NEXUS_DB_ENABLED is False")
                print("  4. Assets are synced with different team_id/org_id")
            
            # Check all static assets
            cur.execute("""
                SELECT COUNT(*) 
                FROM asset_metadata
                WHERE graph_id IS NULL 
                  AND asset_definition_id IS NULL
                  AND actv_ind = TRUE
            """)
            static_count = cur.fetchone()[0]
            print(f"\n📊 Total static assets (graph_id IS NULL): {static_count}")
            
            # Check recent sync activity
            cur.execute("""
                SELECT COUNT(*) 
                FROM asset_metadata
                WHERE graph_id IS NULL 
                  AND asset_definition_id IS NULL
                  AND updt_dttm > NOW() - INTERVAL '1 hour'
            """)
            recent_count = cur.fetchone()[0]
            print(f"📊 Static assets updated in last hour: {recent_count}")
            
    finally:
        conn.close()
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the example-pipelines directory")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
