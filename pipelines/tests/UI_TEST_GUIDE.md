# UI Test Guide: Per-Asset Config with Multi-Graph Assets

## Test Files Created

1. **`ui_test_graph_a.yaml`** - Sales Pipeline Graph
   - Assets: `sales_ingestion_asset`, `sales_transformed_asset`
   - Group: `sales_pipeline`
   - No jobs defined (static assets only)

2. **`ui_test_graph_b.yaml`** - Marketing Pipeline Graph
   - Assets: `marketing_ingestion_asset`, `marketing_analytics_asset`
   - Group: `marketing_pipeline`
   - No jobs defined (static assets only)

## Test Scenario: Create Job from Multiple Graphs

### Step 1: Load the Graphs
1. Ensure both YAML files are in your code location:
   - `/home/ukatru/github/example-pipelines/pipelines/tests/ui_test_graph_a.yaml`
   - `/home/ukatru/github/example-pipelines/pipelines/tests/ui_test_graph_b.yaml`
2. Restart Dagster or reload code locations:
   ```bash
   dagster code-location reload
   ```
3. Verify both graphs appear in the UI:
   - Navigate to "Graphs" or "Assets" section
   - You should see assets from both graphs:
     - From Graph A: `sales_ingestion_asset`, `sales_transformed_asset`
     - From Graph B: `marketing_ingestion_asset`, `marketing_analytics_asset`

### Step 2: Create a Job in UI
1. Navigate to **Job Builder** (or Pipeline Builder → Create Job)
2. Fill in basic job information:
   - **Name**: `ui_test_multi_graph_job`
   - **Description**: "Test job selecting assets from two different graphs"
   - **Team**: Select your team
   - **Code Location**: Select your code location

3. **Select Assets** (This is the key step):
   - In the asset selection interface (Selection Manager), search/select:
     - `sales_ingestion_asset` (from Graph A - sales_pipeline group)
     - `marketing_ingestion_asset` (from Graph B - marketing_pipeline group)
   - **Important**: Select assets from BOTH graphs to test multi-graph scenario
   - You can search by asset name or filter by group (`group:sales_pipeline`, `group:marketing_pipeline`)

4. **Parameter Discovery** (Automatic):
   - After selecting assets, the UI automatically calls `inspectParams` API
   - The backend analyzes both assets and discovers their parameters:
     - `source_bucket` (string, required)
     - `source_path` (string, required)  
     - `source_pattern` (string, required)
     - `target_bucket` (string, required)
   - **Multi-graph handling**: The backend should merge params_schema from assets in different graphs
   - Parameters should appear in the "Parameters" step of the wizard

### Step 3: Test Per-Asset Config UI

#### 3.1 Navigate to Parameters Step
- After selecting assets and proceeding through the wizard
- You'll reach the "Parameters" step
- **Initial State (Simple View)**:
  - You should see a simple parameter form with job-level parameters
  - No tabs visible (progressive disclosure - hidden by default)
  - This is the normal view for single-asset jobs

#### 3.2 Enable Per-Asset Config
- **Look for banner**: "Multi-Asset Job Detected - This job selects 2 assets. Configure per-asset parameters if needed."
- **Click**: "Configure Per-Asset Parameters" button
- **Tabs should appear**:
  - **Shared** tab (job-level parameters) - shows count of parameters
  - **sales_ingestion_asset** tab (monospace font)
  - **marketing_ingestion_asset** tab (monospace font)

#### 3.3 Configure Shared Parameters
1. Click "Shared" tab
2. Fill in default values:
   - `source_bucket`: `my-dagster-poc`
   - `source_path`: `input`
   - `source_pattern`: `.*\\.csv`
   - `target_bucket`: `my-dagster-poc`

#### 3.4 Configure Per-Asset Overrides
1. Click **sales_ingestion_asset** tab
2. Override specific parameters:
   - `source_bucket`: `sales-data-bucket`
   - `source_path`: `sales/input`
   - Leave `source_pattern` and `target_bucket` empty (will use shared values)

3. Click **marketing_ingestion_asset** tab
4. Override different parameters:
   - `source_bucket`: `marketing-data-bucket`
   - `source_path`: `marketing/input`
   - `target_bucket`: `marketing-processed-bucket`
   - Leave `source_pattern` empty (will use shared value)

#### 3.5 Save and Verify
1. Click "Save" or "Submit"
2. Verify the job is created with:
   - `job_overrides`: Shared parameters
   - `ops_config`: Per-asset overrides

### Step 4: Expected YAML Output

After saving, the job should have this structure:

```yaml
jobs:
  - name: ui_test_multi_graph_job
    description: "Test job selecting assets from two different graphs"
    selection: 
      - sales_ingestion_asset
      - marketing_ingestion_asset
    params_schema:
      source_bucket: "string!|my-dagster-poc"
      source_path: "string!|input"
      source_pattern: "string!|.*\\.csv"
      target_bucket: "string!|my-dagster-poc"
    job_overrides:
      source_bucket: "my-dagster-poc"
      source_path: "input"
      source_pattern: ".*\\.csv"
      target_bucket: "my-dagster-poc"
    ops_config:
      sales_ingestion_asset:
        source_bucket: "sales-data-bucket"
        source_path: "sales/input"
      marketing_ingestion_asset:
        source_bucket: "marketing-data-bucket"
        source_path: "marketing/input"
        target_bucket: "marketing-processed-bucket"
```

### Step 5: Verify Parameter Resolution

When the job runs:
- **sales_ingestion_asset** should receive:
  - `source_bucket`: `sales-data-bucket` (from ops_config)
  - `source_path`: `sales/input` (from ops_config)
  - `source_pattern`: `.*\\.csv` (from job_overrides)
  - `target_bucket`: `my-dagster-poc` (from job_overrides)

- **marketing_ingestion_asset** should receive:
  - `source_bucket`: `marketing-data-bucket` (from ops_config)
  - `source_path`: `marketing/input` (from ops_config)
  - `source_pattern`: `.*\\.csv` (from job_overrides)
  - `target_bucket`: `marketing-processed-bucket` (from ops_config)

## Testing Multi-Graph Parameter Schema Merging

### Test Case: Different Parameter Schemas

If you want to test merging different schemas:
1. Modify `ui_test_graph_a.yaml` to add a parameter only for sales assets
2. Modify `ui_test_graph_b.yaml` to add a different parameter only for marketing assets
3. Create a job selecting assets from both graphs
4. Verify the UI shows the union of all parameters

## Troubleshooting

- **Tabs not showing**: Make sure you selected multiple assets (2+)
- **Parameters not saving**: Check browser console for errors
- **Wrong parameters applied**: Verify `ops_config` structure in saved job YAML
