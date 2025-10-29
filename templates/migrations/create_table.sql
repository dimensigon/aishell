-- Migration: Create {{table_name}} table
-- Created: {{timestamp}}

-- @up
CREATE TABLE {{table_name}} (
  id SERIAL PRIMARY KEY,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_{{table_name}}_created_at ON {{table_name}}(created_at);

-- @down
DROP TABLE IF EXISTS {{table_name}} CASCADE;
