from pathlib import Path
from nexus_foundry.dagster import DagsterFactory

# Path to the root of example-pipelines
BASE_DIR = Path(__file__).parent

# Initialize factory
factory = DagsterFactory(BASE_DIR)

# Build configurations (Phase 1 & 2)
show_logs = True
all_configs_raw = factory._load_all_configs(show_logs)
all_configs = factory._apply_overrides(all_configs_raw)

print("\n--- Final Schedules Config ---")
for item in all_configs:
    config = item["config"]
    if "schedules" in config:
        for s in config["schedules"]:
            print(f"Schedule Name: {s['name']}, Target Job: {s.get('job') or s.get('jobs')}")

# Build Definitions (Phase 3)
defs = factory.build_definitions()

print("\n--- Dagster Definitions ---")
print(f"Total Jobs: {len(defs.jobs)}")
job_names = [j.name for j in defs.jobs]
print(f"Job Names: {job_names}")

print(f"\nTotal Schedules: {len(defs.schedules)}")
schedule_names = [s.name for s in defs.schedules]
print(f"Schedule Names: {schedule_names}")

# Check for our missing ones
target_instances = ['uma_poc', 'PROD_HOURLY']
for inst in target_instances:
    found = any(inst in name for name in schedule_names)
    print(f"Instance '{inst}' schedule found: {found}")
