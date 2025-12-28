-- Migration: Add index to {{table_name}}
-- Created: {{timestamp}}

-- @up
-- Create index concurrently (PostgreSQL only, zero-downtime)
CREATE INDEX CONCURRENTLY IF NOT EXISTS {{index_name}}
ON {{table_name}} ({{columns}});

-- @down
DROP INDEX CONCURRENTLY IF EXISTS {{index_name}};
