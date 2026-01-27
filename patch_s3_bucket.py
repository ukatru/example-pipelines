import psycopg2
from psycopg2.extras import DictCursor
import yaml
import os

DB_PARAMS = {
    "dbname": "dpe_framework",
    "user": "dagster",
    "password": "dagster",
    "host": "192.168.2.116",
    "port": "30722"
}

def patch_s3_config():
    print("Connecting to DB...")
    conn = psycopg2.connect(**DB_PARAMS)
    try:
        cur = conn.cursor(cursor_factory=DictCursor)
        
        # Fetch Visual Pipelines
        cur.execute("SELECT id, asset_nm, asset_yaml FROM etl_asset_definition WHERE asset_type = 'pipeline'")
        rows = cur.fetchall()
        
        for row in rows:
            print(f"Checking Pipeline: {row['asset_nm']}")
            yaml_content = row['asset_yaml']
            if not yaml_content: continue
            
            data = yaml.safe_load(yaml_content)
            assets = data.get('assets', [])
            
            modified = False
            for asset in assets:
                # Patch function to flatten and rename
                def patch_conf(conf, context_name):
                    nonlocal modified
                    # Flatten configs if present
                    if 'configs' in conf and isinstance(conf['configs'], dict):
                        print(f"  - Patching {asset['name']} ({context_name}): flattening 'configs'")
                        nested = conf.pop('configs')
                        conf.update(nested)
                        modified = True
                    
                    # Rename bucket -> bucket_name
                    if 'bucket' in conf:
                         print(f"  - Patching {asset['name']} ({context_name}): renaming 'bucket' to 'bucket_name'")
                         conf['bucket_name'] = conf.pop('bucket')
                         modified = True
                
                # Check Target S3
                target = asset.get('target', {})
                if target.get('type') == 'S3':
                    patch_conf(target, 'Target')

                # Check Source S3
                source = asset.get('source', {})
                if source.get('type') == 'S3':
                     patch_conf(source, 'Source')
            
            if modified:
                new_yaml = yaml.dump(data)
                cur.execute(
                    "UPDATE etl_asset_definition SET asset_yaml = %s WHERE id = %s",
                    (new_yaml, row['id'])
                )
                print("  -> Updated DB record.")
            else:
                print("  -> No changes needed.")
        
        conn.commit()
        print("Patch complete.")

    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    patch_s3_config()
