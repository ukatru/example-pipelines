-- Query to check if static assets from ui_test_graph_a.yaml and ui_test_graph_b.yaml are synced
-- Static assets have graph_id IS NULL and asset_definition_id IS NULL

-- Check for assets from Graph A (sales_pipeline)
SELECT 
    id,
    asset_key,
    asset_name,
    group_name,
    team_nm,
    graph_id,
    asset_definition_id,
    partition_type,
    compute_kind,
    actv_ind,
    creat_dttm,
    updt_dttm
FROM asset_metadata
WHERE asset_key IN (
    'sales_ingestion_asset',
    'sales_transformed_asset',
    'marketing_ingestion_asset',
    'marketing_analytics_asset'
)
ORDER BY asset_key;

-- Check all static assets (graph_id IS NULL and asset_definition_id IS NULL)
SELECT 
    COUNT(*) as total_static_assets,
    COUNT(DISTINCT group_name) as distinct_groups
FROM asset_metadata
WHERE graph_id IS NULL 
  AND asset_definition_id IS NULL
  AND actv_ind = TRUE;

-- Check if sync ran recently (check for recent updates)
SELECT 
    asset_key,
    asset_name,
    group_name,
    updt_dttm,
    creat_dttm
FROM asset_metadata
WHERE graph_id IS NULL 
  AND asset_definition_id IS NULL
  AND updt_dttm > NOW() - INTERVAL '1 hour'
ORDER BY updt_dttm DESC
LIMIT 20;
