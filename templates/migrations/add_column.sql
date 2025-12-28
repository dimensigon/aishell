-- Migration: Add {{column_name}} to {{table_name}}
-- Created: {{timestamp}}

-- @up
-- Step 1: Add column as nullable
ALTER TABLE {{table_name}} ADD COLUMN {{column_name}} {{column_type}};

-- Step 2: Backfill data (if needed)
-- UPDATE {{table_name}} SET {{column_name}} = {{default_value}} WHERE {{column_name}} IS NULL;

-- Step 3: Add constraint (if needed)
-- ALTER TABLE {{table_name}} ALTER COLUMN {{column_name}} SET NOT NULL;

-- @down
ALTER TABLE {{table_name}} DROP COLUMN {{column_name}};
