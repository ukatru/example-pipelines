from nexus_core.core.provider import JobParamsProvider
from pathlib import Path
import os
import json

def check_sftp_conn():
    provider = JobParamsProvider(Path("."))
    try:
        conn_data = provider.get_connection_config("sftp_prod")
        print(f"Connection Name: {conn_data['conn_nm']}")
        print(f"Connection Type: {conn_data['conn_type']}")
        print("Config JSON:")
        print(json.dumps(conn_data['config_json'], indent=2))
        
        resolved = provider.get_conn("sftp_prod")
        print("\nFully Resolved (Hydrated) Config:")
        print(json.dumps(resolved, indent=2))
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_sftp_conn()
