import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

db_params = {
    "dbname": os.environ.get("POSTGRES_DB"),
    "user": os.environ.get("POSTGRES_USER"),
    "password": os.environ.get("POSTGRES_PASSWORD"),
    "host": os.environ.get("POSTGRES_HOST", "localhost"),
    "port": os.environ.get("POSTGRES_PORT", "5432")
}

try:
    conn = psycopg2.connect(**db_params)
    with conn.cursor() as cur:
        cur.execute("SELECT conn_nm, conn_type, config_json FROM etl_connection")
        print("Connections in DB:")
        for row in cur.fetchall():
            print(f"Name: {row[0]}, Type: {row[1]}, Config: {row[2]}")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
