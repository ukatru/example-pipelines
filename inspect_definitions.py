from definitions import defs
import json

def inspect():
    print("=== Nexus Foundry Inspection ===")
    
    # 1. Inspect Assets
    # 1. Inspect Assets
    repo = defs.get_repository_def()
    assets = repo.get_all_assets()
    print(f"\nTotal Assets: {len(assets)}")
    for a in sorted([str(k.key.path) for k in assets]):
        print(f"  - {a}")

    # 2. Inspect Jobs
    jobs = defs.get_job_configs()
    print(f"\nTotal Jobs: {len(jobs)}")
    for j_nm in sorted(jobs.keys()):
        print(f"  - {j_nm}")

    # 3. Inspect Schedules
    schedules = defs.get_schedule_configs()
    print(f"\nTotal Schedules: {len(schedules)}")
    for s_nm in sorted(schedules.keys()):
        print(f"  - {s_nm}")

if __name__ == "__main__":
    inspect()
