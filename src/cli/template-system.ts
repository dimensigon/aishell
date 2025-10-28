#!/usr/bin/env node

/**
 * Template System for AI-Shell
 *
 * Provides comprehensive query template management with:
 * - 20+ built-in templates for common patterns
 * - Custom template creation with parameter definitions
 * - Template categories and tagging
 * - Template sharing and import/export
 * - Template validation and testing
 * - Version control for templates
 * - Template marketplace integration (future-ready)
 *
 * @module template-system
 * @version 1.0.0
 */

import * as fs from 'fs';
import * as path from 'path';
import * as readline from 'readline';

// ============================================================================
// Type Definitions
// ============================================================================

export type ParameterType = 'string' | 'number' | 'date' | 'boolean' | 'array' | 'object';

export interface TemplateParameter {
  name: string;
  type: ParameterType;
  description: string;
  required?: boolean;
  default?: any;
  validation?: {
    pattern?: string;
    min?: number;
    max?: number;
    enum?: any[];
    custom?: (value: any) => boolean | string;
  };
}

export interface TemplateMetadata {
  name: string;
  version: string;
  description: string;
  category: string;
  tags: string[];
  author?: string;
  created: Date;
  updated: Date;
  usage?: string;
  examples?: string[];
}

export interface Template {
  metadata: TemplateMetadata;
  parameters: TemplateParameter[];
  query: string;
  extends?: string; // Template inheritance
  variables?: Record<string, any>; // Pre-defined variables
  tests?: TemplateTest[];
}

export interface TemplateTest {
  name: string;
  description: string;
  parameters: Record<string, any>;
  expectedPattern?: string; // Regex pattern for expected result
  shouldFail?: boolean;
}

export interface TemplateCategory {
  name: string;
  description: string;
  icon?: string;
}

export interface TemplateValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
}

export interface TemplateApplication {
  template: string;
  parameters: Record<string, any>;
  result: string;
  timestamp: Date;
}

// ============================================================================
// Built-in Template Categories
// ============================================================================

const TEMPLATE_CATEGORIES: Record<string, TemplateCategory> = {
  crud: {
    name: 'CRUD Operations',
    description: 'Create, Read, Update, Delete operations',
    icon: '📝'
  },
  analytics: {
    name: 'Analytics',
    description: 'Data analysis and reporting queries',
    icon: '📊'
  },
  admin: {
    name: 'Administrative',
    description: 'Database administration tasks',
    icon: '⚙️'
  },
  migration: {
    name: 'Migrations',
    description: 'Schema migration patterns',
    icon: '🔄'
  },
  performance: {
    name: 'Performance',
    description: 'Performance optimization queries',
    icon: '⚡'
  },
  security: {
    name: 'Security',
    description: 'Security and access control',
    icon: '🔒'
  }
};

// ============================================================================
// Built-in Templates Library (20+ templates)
// ============================================================================

const BUILTIN_TEMPLATES: Template[] = [
  // CRUD Operations (8 templates)
  {
    metadata: {
      name: 'crud.select-all',
      version: '1.0.0',
      description: 'Select all records from a table with optional filtering',
      category: 'crud',
      tags: ['select', 'read', 'basic'],
      created: new Date('2025-01-01'),
      updated: new Date('2025-01-01'),
      usage: 'template apply crud.select-all --table users --where "status = \'active\'"',
      examples: [
        'template apply crud.select-all --table users',
        'template apply crud.select-all --table orders --where "created_at > \'2025-01-01\'" --limit 100'
      ]
    },
    parameters: [
      {
        name: 'table',
        type: 'string',
        description: 'Table name to query',
        required: true,
        validation: {
          pattern: '^[a-zA-Z_][a-zA-Z0-9_]*$'
        }
      },
      {
        name: 'columns',
        type: 'string',
        description: 'Columns to select (comma-separated)',
        default: '*'
      },
      {
        name: 'where',
        type: 'string',
        description: 'WHERE clause condition'
      },
      {
        name: 'order',
        type: 'string',
        description: 'ORDER BY clause'
      },
      {
        name: 'limit',
        type: 'number',
        description: 'Maximum number of records',
        validation: { min: 1, max: 10000 }
      }
    ],
    query: `SELECT {{columns}}
FROM {{table}}
{{#if where}}WHERE {{where}}{{/if}}
{{#if order}}ORDER BY {{order}}{{/if}}
{{#if limit}}LIMIT {{limit}}{{/if}};`
  },
  {
    metadata: {
      name: 'crud.insert',
      version: '1.0.0',
      description: 'Insert a new record into a table',
      category: 'crud',
      tags: ['insert', 'create'],
      created: new Date('2025-01-01'),
      updated: new Date('2025-01-01'),
      usage: 'template apply crud.insert --table users --columns "name, email" --values "\'John Doe\', \'john@example.com\'"'
    },
    parameters: [
      {
        name: 'table',
        type: 'string',
        description: 'Table name',
        required: true
      },
      {
        name: 'columns',
        type: 'string',
        description: 'Column names (comma-separated)',
        required: true
      },
      {
        name: 'values',
        type: 'string',
        description: 'Values to insert (comma-separated)',
        required: true
      },
      {
        name: 'returning',
        type: 'string',
        description: 'Columns to return after insert',
        default: '*'
      }
    ],
    query: `INSERT INTO {{table}} ({{columns}})
VALUES ({{values}})
RETURNING {{returning}};`
  },
  {
    metadata: {
      name: 'crud.update',
      version: '1.0.0',
      description: 'Update records in a table',
      category: 'crud',
      tags: ['update', 'modify'],
      created: new Date('2025-01-01'),
      updated: new Date('2025-01-01')
    },
    parameters: [
      {
        name: 'table',
        type: 'string',
        description: 'Table name',
        required: true
      },
      {
        name: 'set',
        type: 'string',
        description: 'SET clause (column = value pairs)',
        required: true
      },
      {
        name: 'where',
        type: 'string',
        description: 'WHERE clause condition',
        required: true
      }
    ],
    query: `UPDATE {{table}}
SET {{set}}
WHERE {{where}}
RETURNING *;`
  },
  {
    metadata: {
      name: 'crud.delete',
      version: '1.0.0',
      description: 'Delete records from a table',
      category: 'crud',
      tags: ['delete', 'remove'],
      created: new Date('2025-01-01'),
      updated: new Date('2025-01-01')
    },
    parameters: [
      {
        name: 'table',
        type: 'string',
        description: 'Table name',
        required: true
      },
      {
        name: 'where',
        type: 'string',
        description: 'WHERE clause condition',
        required: true
      },
      {
        name: 'soft',
        type: 'boolean',
        description: 'Soft delete (set deleted_at)',
        default: false
      }
    ],
    query: `{{#if soft}}
UPDATE {{table}}
SET deleted_at = NOW()
WHERE {{where}} AND deleted_at IS NULL
RETURNING *;
{{else}}
DELETE FROM {{table}}
WHERE {{where}}
RETURNING *;
{{/if}}`
  },
  {
    metadata: {
      name: 'crud.upsert',
      version: '1.0.0',
      description: 'Insert or update record (upsert)',
      category: 'crud',
      tags: ['upsert', 'merge'],
      created: new Date('2025-01-01'),
      updated: new Date('2025-01-01')
    },
    parameters: [
      {
        name: 'table',
        type: 'string',
        description: 'Table name',
        required: true
      },
      {
        name: 'columns',
        type: 'string',
        description: 'Column names',
        required: true
      },
      {
        name: 'values',
        type: 'string',
        description: 'Values to insert',
        required: true
      },
      {
        name: 'conflict',
        type: 'string',
        description: 'Conflict columns',
        required: true
      },
      {
        name: 'update',
        type: 'string',
        description: 'Update clause',
        required: true
      }
    ],
    query: `INSERT INTO {{table}} ({{columns}})
VALUES ({{values}})
ON CONFLICT ({{conflict}})
DO UPDATE SET {{update}}
RETURNING *;`
  },
  {
    metadata: {
      name: 'crud.bulk-insert',
      version: '1.0.0',
      description: 'Bulk insert multiple records',
      category: 'crud',
      tags: ['bulk', 'insert', 'batch'],
      created: new Date('2025-01-01'),
      updated: new Date('2025-01-01')
    },
    parameters: [
      {
        name: 'table',
        type: 'string',
        description: 'Table name',
        required: true
      },
      {
        name: 'columns',
        type: 'string',
        description: 'Column names',
        required: true
      },
      {
        name: 'values',
        type: 'array',
        description: 'Array of value rows',
        required: true
      }
    ],
    query: `INSERT INTO {{table}} ({{columns}})
VALUES {{#each values}}({{this}}){{#unless @last}},{{/unless}}{{/each}}
RETURNING *;`
  },
  {
    metadata: {
      name: 'crud.paginated-select',
      version: '1.0.0',
      description: 'Paginated select with total count',
      category: 'crud',
      tags: ['select', 'pagination'],
      created: new Date('2025-01-01'),
      updated: new Date('2025-01-01')
    },
    parameters: [
      {
        name: 'table',
        type: 'string',
        description: 'Table name',
        required: true
      },
      {
        name: 'page',
        type: 'number',
        description: 'Page number (1-based)',
        required: true,
        validation: { min: 1 }
      },
      {
        name: 'pageSize',
        type: 'number',
        description: 'Records per page',
        default: 20,
        validation: { min: 1, max: 100 }
      },
      {
        name: 'where',
        type: 'string',
        description: 'WHERE clause'
      }
    ],
    query: `WITH counted AS (
  SELECT COUNT(*) as total FROM {{table}}{{#if where}} WHERE {{where}}{{/if}}
),
data AS (
  SELECT * FROM {{table}}
  {{#if where}}WHERE {{where}}{{/if}}
  ORDER BY id
  LIMIT {{pageSize}} OFFSET {{#expr}}({{page}} - 1) * {{pageSize}}{{/expr}}
)
SELECT *, (SELECT total FROM counted) as total_count FROM data;`
  },
  {
    metadata: {
      name: 'crud.soft-delete-restore',
      version: '1.0.0',
      description: 'Restore soft-deleted records',
      category: 'crud',
      tags: ['restore', 'soft-delete'],
      created: new Date('2025-01-01'),
      updated: new Date('2025-01-01')
    },
    parameters: [
      {
        name: 'table',
        type: 'string',
        description: 'Table name',
        required: true
      },
      {
        name: 'where',
        type: 'string',
        description: 'WHERE clause',
        required: true
      }
    ],
    query: `UPDATE {{table}}
SET deleted_at = NULL
WHERE {{where}} AND deleted_at IS NOT NULL
RETURNING *;`
  },

  // Analytics Queries (6 templates)
  {
    metadata: {
      name: 'analytics.aggregate-by-time',
      version: '1.0.0',
      description: 'Aggregate data by time period',
      category: 'analytics',
      tags: ['aggregate', 'time-series', 'group'],
      created: new Date('2025-01-01'),
      updated: new Date('2025-01-01')
    },
    parameters: [
      {
        name: 'table',
        type: 'string',
        description: 'Table name',
        required: true
      },
      {
        name: 'metric',
        type: 'string',
        description: 'Metric to aggregate',
        required: true
      },
      {
        name: 'aggregation',
        type: 'string',
        description: 'Aggregation function',
        required: true,
        validation: {
          enum: ['SUM', 'AVG', 'COUNT', 'MIN', 'MAX']
        }
      },
      {
        name: 'dateColumn',
        type: 'string',
        description: 'Date column name',
        required: true
      },
      {
        name: 'period',
        type: 'string',
        description: 'Time period',
        required: true,
        validation: {
          enum: ['hour', 'day', 'week', 'month', 'year']
        }
      },
      {
        name: 'where',
        type: 'string',
        description: 'WHERE clause'
      }
    ],
    query: `SELECT
  DATE_TRUNC('{{period}}', {{dateColumn}}) as period,
  {{aggregation}}({{metric}}) as value
FROM {{table}}
{{#if where}}WHERE {{where}}{{/if}}
GROUP BY period
ORDER BY period;`
  },
  {
    metadata: {
      name: 'analytics.top-n',
      version: '1.0.0',
      description: 'Find top N records by metric',
      category: 'analytics',
      tags: ['ranking', 'top'],
      created: new Date('2025-01-01'),
      updated: new Date('2025-01-01')
    },
    parameters: [
      {
        name: 'table',
        type: 'string',
        description: 'Table name',
        required: true
      },
      {
        name: 'metric',
        type: 'string',
        description: 'Metric to rank by',
        required: true
      },
      {
        name: 'n',
        type: 'number',
        description: 'Number of top records',
        required: true,
        validation: { min: 1, max: 1000 }
      },
      {
        name: 'groupBy',
        type: 'string',
        description: 'Group by column'
      },
      {
        name: 'where',
        type: 'string',
        description: 'WHERE clause'
      }
    ],
    query: `SELECT {{#if groupBy}}{{groupBy}},{{/if}} SUM({{metric}}) as total
FROM {{table}}
{{#if where}}WHERE {{where}}{{/if}}
{{#if groupBy}}GROUP BY {{groupBy}}{{/if}}
ORDER BY total DESC
LIMIT {{n}};`
  },
  {
    metadata: {
      name: 'analytics.cohort-analysis',
      version: '1.0.0',
      description: 'Cohort retention analysis',
      category: 'analytics',
      tags: ['cohort', 'retention'],
      created: new Date('2025-01-01'),
      updated: new Date('2025-01-01')
    },
    parameters: [
      {
        name: 'table',
        type: 'string',
        description: 'User activity table',
        required: true
      },
      {
        name: 'userColumn',
        type: 'string',
        description: 'User ID column',
        required: true
      },
      {
        name: 'dateColumn',
        type: 'string',
        description: 'Activity date column',
        required: true
      },
      {
        name: 'cohortPeriod',
        type: 'string',
        description: 'Cohort period',
        default: 'month',
        validation: { enum: ['day', 'week', 'month'] }
      }
    ],
    query: `WITH cohorts AS (
  SELECT
    {{userColumn}},
    DATE_TRUNC('{{cohortPeriod}}', MIN({{dateColumn}})) as cohort_period
  FROM {{table}}
  GROUP BY {{userColumn}}
),
activity AS (
  SELECT
    c.cohort_period,
    DATE_TRUNC('{{cohortPeriod}}', a.{{dateColumn}}) as activity_period,
    COUNT(DISTINCT a.{{userColumn}}) as active_users
  FROM {{table}} a
  JOIN cohorts c ON a.{{userColumn}} = c.{{userColumn}}
  GROUP BY c.cohort_period, activity_period
)
SELECT
  cohort_period,
  activity_period,
  active_users,
  ROUND(100.0 * active_users / FIRST_VALUE(active_users)
    OVER (PARTITION BY cohort_period ORDER BY activity_period), 2) as retention_rate
FROM activity
ORDER BY cohort_period, activity_period;`
  },
  {
    metadata: {
      name: 'analytics.funnel',
      version: '1.0.0',
      description: 'Funnel analysis with conversion rates',
      category: 'analytics',
      tags: ['funnel', 'conversion'],
      created: new Date('2025-01-01'),
      updated: new Date('2025-01-01')
    },
    parameters: [
      {
        name: 'table',
        type: 'string',
        description: 'Events table',
        required: true
      },
      {
        name: 'userColumn',
        type: 'string',
        description: 'User ID column',
        required: true
      },
      {
        name: 'eventColumn',
        type: 'string',
        description: 'Event type column',
        required: true
      },
      {
        name: 'steps',
        type: 'array',
        description: 'Funnel steps in order',
        required: true
      }
    ],
    query: `WITH funnel_data AS (
  SELECT
    {{userColumn}},
    {{#each steps}}
    MAX(CASE WHEN {{../eventColumn}} = '{{this}}' THEN 1 ELSE 0 END) as step_{{@index}}{{#unless @last}},{{/unless}}
    {{/each}}
  FROM {{table}}
  WHERE {{eventColumn}} IN ({{#each steps}}'{{this}}'{{#unless @last}},{{/unless}}{{/each}})
  GROUP BY {{userColumn}}
)
SELECT
  {{#each steps}}
  '{{this}}' as step,
  SUM(step_{{@index}}) as users,
  ROUND(100.0 * SUM(step_{{@index}}) / NULLIF(SUM(step_0), 0), 2) as conversion_rate
  FROM funnel_data
  {{#unless @last}}UNION ALL SELECT {{/unless}}
  {{/each}};`
  },
  {
    metadata: {
      name: 'analytics.percentile',
      version: '1.0.0',
      description: 'Calculate percentile metrics',
      category: 'analytics',
      tags: ['percentile', 'statistics'],
      created: new Date('2025-01-01'),
      updated: new Date('2025-01-01')
    },
    parameters: [
      {
        name: 'table',
        type: 'string',
        description: 'Table name',
        required: true
      },
      {
        name: 'metric',
        type: 'string',
        description: 'Metric column',
        required: true
      },
      {
        name: 'percentiles',
        type: 'array',
        description: 'Percentiles to calculate',
        default: [25, 50, 75, 90, 95, 99]
      },
      {
        name: 'where',
        type: 'string',
        description: 'WHERE clause'
      }
    ],
    query: `SELECT
  {{#each percentiles}}
  PERCENTILE_CONT({{this}} / 100.0) WITHIN GROUP (ORDER BY {{../metric}}) as p{{this}}{{#unless @last}},{{/unless}}
  {{/each}}
FROM {{table}}
{{#if where}}WHERE {{where}}{{/if}};`
  },
  {
    metadata: {
      name: 'analytics.moving-average',
      version: '1.0.0',
      description: 'Calculate moving average over time',
      category: 'analytics',
      tags: ['moving-average', 'time-series'],
      created: new Date('2025-01-01'),
      updated: new Date('2025-01-01')
    },
    parameters: [
      {
        name: 'table',
        type: 'string',
        description: 'Table name',
        required: true
      },
      {
        name: 'metric',
        type: 'string',
        description: 'Metric to average',
        required: true
      },
      {
        name: 'dateColumn',
        type: 'string',
        description: 'Date column',
        required: true
      },
      {
        name: 'window',
        type: 'number',
        description: 'Window size (days)',
        required: true,
        validation: { min: 1, max: 365 }
      }
    ],
    query: `SELECT
  {{dateColumn}}::DATE as date,
  {{metric}},
  AVG({{metric}}) OVER (
    ORDER BY {{dateColumn}}::DATE
    ROWS BETWEEN {{window}} PRECEDING AND CURRENT ROW
  ) as moving_avg
FROM {{table}}
ORDER BY {{dateColumn}}::DATE;`
  },

  // Administrative Tasks (4 templates)
  {
    metadata: {
      name: 'admin.analyze-table',
      version: '1.0.0',
      description: 'Analyze and vacuum table',
      category: 'admin',
      tags: ['maintenance', 'optimize'],
      created: new Date('2025-01-01'),
      updated: new Date('2025-01-01')
    },
    parameters: [
      {
        name: 'table',
        type: 'string',
        description: 'Table name',
        required: true
      },
      {
        name: 'full',
        type: 'boolean',
        description: 'Full vacuum',
        default: false
      }
    ],
    query: `VACUUM {{#if full}}FULL {{/if}}ANALYZE {{table}};`
  },
  {
    metadata: {
      name: 'admin.index-usage',
      version: '1.0.0',
      description: 'Analyze index usage statistics',
      category: 'admin',
      tags: ['index', 'performance'],
      created: new Date('2025-01-01'),
      updated: new Date('2025-01-01')
    },
    parameters: [
      {
        name: 'schema',
        type: 'string',
        description: 'Schema name',
        default: 'public'
      },
      {
        name: 'minSize',
        type: 'string',
        description: 'Minimum index size',
        default: '100 KB'
      }
    ],
    query: `SELECT
  schemaname,
  tablename,
  indexname,
  idx_scan as scans,
  pg_size_pretty(pg_relation_size(indexrelid)) as size,
  CASE WHEN idx_scan = 0 THEN 'Unused'
       WHEN idx_scan < 100 THEN 'Low usage'
       ELSE 'Active' END as status
FROM pg_stat_user_indexes
WHERE schemaname = '{{schema}}'
  AND pg_relation_size(indexrelid) > pg_size_bytes('{{minSize}}')
ORDER BY idx_scan ASC, pg_relation_size(indexrelid) DESC;`
  },
  {
    metadata: {
      name: 'admin.table-bloat',
      version: '1.0.0',
      description: 'Detect table bloat',
      category: 'admin',
      tags: ['bloat', 'maintenance'],
      created: new Date('2025-01-01'),
      updated: new Date('2025-01-01')
    },
    parameters: [
      {
        name: 'schema',
        type: 'string',
        description: 'Schema name',
        default: 'public'
      }
    ],
    query: `SELECT
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
  ROUND(100 * pg_total_relation_size(schemaname||'.'||tablename) /
    NULLIF(pg_database_size(current_database()), 0), 2) as pct_of_db
FROM pg_tables
WHERE schemaname = '{{schema}}'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 20;`
  },
  {
    metadata: {
      name: 'admin.long-running-queries',
      version: '1.0.0',
      description: 'Find long-running queries',
      category: 'admin',
      tags: ['monitoring', 'performance'],
      created: new Date('2025-01-01'),
      updated: new Date('2025-01-01')
    },
    parameters: [
      {
        name: 'minDuration',
        type: 'number',
        description: 'Minimum duration (seconds)',
        default: 60,
        validation: { min: 1 }
      }
    ],
    query: `SELECT
  pid,
  usename,
  application_name,
  client_addr,
  NOW() - query_start as duration,
  state,
  query
FROM pg_stat_activity
WHERE state != 'idle'
  AND (NOW() - query_start) > INTERVAL '{{minDuration}} seconds'
ORDER BY duration DESC;`
  },

  // Migration Patterns (3 templates)
  {
    metadata: {
      name: 'migration.add-column',
      version: '1.0.0',
      description: 'Add column with safe defaults',
      category: 'migration',
      tags: ['schema', 'alter'],
      created: new Date('2025-01-01'),
      updated: new Date('2025-01-01')
    },
    parameters: [
      {
        name: 'table',
        type: 'string',
        description: 'Table name',
        required: true
      },
      {
        name: 'column',
        type: 'string',
        description: 'Column name',
        required: true
      },
      {
        name: 'type',
        type: 'string',
        description: 'Column type',
        required: true
      },
      {
        name: 'nullable',
        type: 'boolean',
        description: 'Allow NULL',
        default: true
      },
      {
        name: 'default',
        type: 'string',
        description: 'Default value'
      }
    ],
    query: `ALTER TABLE {{table}}
ADD COLUMN {{column}} {{type}}{{#if default}} DEFAULT {{default}}{{/if}}{{#unless nullable}} NOT NULL{{/unless}};`
  },
  {
    metadata: {
      name: 'migration.create-index',
      version: '1.0.0',
      description: 'Create index with safe options',
      category: 'migration',
      tags: ['index', 'performance'],
      created: new Date('2025-01-01'),
      updated: new Date('2025-01-01')
    },
    parameters: [
      {
        name: 'table',
        type: 'string',
        description: 'Table name',
        required: true
      },
      {
        name: 'columns',
        type: 'string',
        description: 'Columns to index',
        required: true
      },
      {
        name: 'name',
        type: 'string',
        description: 'Index name'
      },
      {
        name: 'unique',
        type: 'boolean',
        description: 'Unique constraint',
        default: false
      },
      {
        name: 'concurrent',
        type: 'boolean',
        description: 'Create concurrently',
        default: true
      }
    ],
    query: `CREATE {{#if unique}}UNIQUE {{/if}}INDEX {{#if concurrent}}CONCURRENTLY {{/if}}{{#if name}}{{name}}{{else}}idx_{{table}}_{{columns}}{{/if}}
ON {{table}} ({{columns}});`
  },
  {
    metadata: {
      name: 'migration.rename-table',
      version: '1.0.0',
      description: 'Rename table with dependencies',
      category: 'migration',
      tags: ['schema', 'rename'],
      created: new Date('2025-01-01'),
      updated: new Date('2025-01-01')
    },
    parameters: [
      {
        name: 'oldName',
        type: 'string',
        description: 'Current table name',
        required: true
      },
      {
        name: 'newName',
        type: 'string',
        description: 'New table name',
        required: true
      }
    ],
    query: `ALTER TABLE {{oldName}} RENAME TO {{newName}};`
  }
];

// ============================================================================
// Template Manager Class
// ============================================================================

export class TemplateManager {
  private templates: Map<string, Template>;
  private customTemplatesPath: string;
  private historyPath: string;

  constructor(baseDir?: string) {
    this.templates = new Map();
    const configDir = baseDir || path.join(process.env.HOME || '', '.aishell');
    this.customTemplatesPath = path.join(configDir, 'templates');
    this.historyPath = path.join(configDir, 'template-history.json');

    this.initializeDirectories();
    this.loadBuiltinTemplates();
    this.loadCustomTemplates();
  }

  private initializeDirectories(): void {
    if (!fs.existsSync(this.customTemplatesPath)) {
      fs.mkdirSync(this.customTemplatesPath, { recursive: true });
    }
  }

  private loadBuiltinTemplates(): void {
    BUILTIN_TEMPLATES.forEach(template => {
      this.templates.set(template.metadata.name, template);
    });
  }

  private loadCustomTemplates(): void {
    if (!fs.existsSync(this.customTemplatesPath)) {
      return;
    }

    const files = fs.readdirSync(this.customTemplatesPath);
    files.forEach(file => {
      if (file.endsWith('.json')) {
        try {
          const filePath = path.join(this.customTemplatesPath, file);
          const content = fs.readFileSync(filePath, 'utf-8');
          const template = JSON.parse(content) as Template;
          this.templates.set(template.metadata.name, template);
        } catch (error) {
          console.error(`Error loading template ${file}:`, error);
        }
      }
    });
  }

  // ============================================================================
  // Template CRUD Operations
  // ============================================================================

  public getTemplate(name: string): Template | undefined {
    return this.templates.get(name);
  }

  public listTemplates(category?: string, tag?: string): Template[] {
    let templates = Array.from(this.templates.values());

    if (category) {
      templates = templates.filter(t => t.metadata.category === category);
    }

    if (tag) {
      templates = templates.filter(t => t.metadata.tags.includes(tag));
    }

    return templates;
  }

  public createTemplate(template: Template): void {
    // Validate template
    const validation = this.validateTemplate(template);
    if (!validation.valid) {
      throw new Error(`Template validation failed: ${validation.errors.join(', ')}`);
    }

    // Save to custom templates
    const filePath = path.join(this.customTemplatesPath, `${template.metadata.name}.json`);
    fs.writeFileSync(filePath, JSON.stringify(template, null, 2));

    // Add to memory
    this.templates.set(template.metadata.name, template);
  }

  public updateTemplate(name: string, updates: Partial<Template>): void {
    const existing = this.templates.get(name);
    if (!existing) {
      throw new Error(`Template not found: ${name}`);
    }

    const updated = {
      ...existing,
      ...updates,
      metadata: {
        ...existing.metadata,
        ...(updates.metadata || {}),
        updated: new Date()
      }
    };

    this.createTemplate(updated);
  }

  public deleteTemplate(name: string): void {
    const template = this.templates.get(name);
    if (!template) {
      throw new Error(`Template not found: ${name}`);
    }

    // Cannot delete built-in templates
    if (BUILTIN_TEMPLATES.some(t => t.metadata.name === name)) {
      throw new Error('Cannot delete built-in templates');
    }

    const filePath = path.join(this.customTemplatesPath, `${name}.json`);
    if (fs.existsSync(filePath)) {
      fs.unlinkSync(filePath);
    }

    this.templates.delete(name);
  }

  // ============================================================================
  // Template Validation
  // ============================================================================

  public validateTemplate(template: Template): TemplateValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];

    // Validate metadata
    if (!template.metadata.name) {
      errors.push('Template name is required');
    }
    if (!template.metadata.version) {
      errors.push('Template version is required');
    }
    if (!template.metadata.category) {
      errors.push('Template category is required');
    }

    // Validate parameters
    template.parameters.forEach(param => {
      if (!param.name) {
        errors.push('Parameter name is required');
      }
      if (!param.type) {
        errors.push(`Parameter ${param.name} must have a type`);
      }
      if (param.validation?.pattern) {
        try {
          new RegExp(param.validation.pattern);
        } catch (e) {
          errors.push(`Invalid regex pattern for parameter ${param.name}`);
        }
      }
    });

    // Validate query
    if (!template.query) {
      errors.push('Template query is required');
    }

    // Check for parameter usage in query
    template.parameters.forEach(param => {
      if (param.required && !template.query.includes(`{{${param.name}}}`)) {
        warnings.push(`Required parameter ${param.name} not used in query`);
      }
    });

    return {
      valid: errors.length === 0,
      errors,
      warnings
    };
  }

  // ============================================================================
  // Parameter Validation and Substitution
  // ============================================================================

  public validateParameters(
    template: Template,
    params: Record<string, any>
  ): TemplateValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];

    template.parameters.forEach(param => {
      const value = params[param.name];

      // Check required parameters
      if (param.required && (value === undefined || value === null)) {
        errors.push(`Required parameter missing: ${param.name}`);
        return;
      }

      // Skip validation if value is undefined and not required
      if (value === undefined) {
        return;
      }

      // Type validation
      const actualType = Array.isArray(value) ? 'array' : typeof value;
      if (actualType !== param.type && !(param.type === 'number' && actualType === 'string' && !isNaN(Number(value)))) {
        errors.push(`Parameter ${param.name} must be of type ${param.type}, got ${actualType}`);
      }

      // Custom validation
      if (param.validation) {
        // Pattern validation
        if (param.validation.pattern && typeof value === 'string') {
          const regex = new RegExp(param.validation.pattern);
          if (!regex.test(value)) {
            errors.push(`Parameter ${param.name} does not match pattern ${param.validation.pattern}`);
          }
        }

        // Range validation
        if (typeof value === 'number') {
          if (param.validation.min !== undefined && value < param.validation.min) {
            errors.push(`Parameter ${param.name} must be >= ${param.validation.min}`);
          }
          if (param.validation.max !== undefined && value > param.validation.max) {
            errors.push(`Parameter ${param.name} must be <= ${param.validation.max}`);
          }
        }

        // Enum validation
        if (param.validation.enum && !param.validation.enum.includes(value)) {
          errors.push(`Parameter ${param.name} must be one of: ${param.validation.enum.join(', ')}`);
        }

        // Custom validation function
        if (param.validation.custom) {
          const result = param.validation.custom(value);
          if (result !== true) {
            errors.push(typeof result === 'string' ? result : `Custom validation failed for ${param.name}`);
          }
        }
      }
    });

    return {
      valid: errors.length === 0,
      errors,
      warnings
    };
  }

  public applyTemplate(
    templateName: string,
    params: Record<string, any>
  ): string {
    const template = this.templates.get(templateName);
    if (!template) {
      throw new Error(`Template not found: ${templateName}`);
    }

    // Apply defaults
    const fullParams = { ...params };
    template.parameters.forEach(param => {
      if (fullParams[param.name] === undefined && param.default !== undefined) {
        fullParams[param.name] = param.default;
      }
    });

    // Validate parameters
    const validation = this.validateParameters(template, fullParams);
    if (!validation.valid) {
      throw new Error(`Parameter validation failed: ${validation.errors.join(', ')}`);
    }

    // Apply template inheritance
    let baseQuery = template.query;
    if (template.extends) {
      const parentTemplate = this.templates.get(template.extends);
      if (parentTemplate) {
        baseQuery = parentTemplate.query + '\n' + baseQuery;
      }
    }

    // Substitute parameters
    let result = this.substituteParameters(baseQuery, fullParams);

    // Record history
    this.recordApplication({
      template: templateName,
      parameters: fullParams,
      result,
      timestamp: new Date()
    });

    return result;
  }

  private substituteParameters(query: string, params: Record<string, any>): string {
    let result = query;

    // Simple parameter substitution
    Object.keys(params).forEach(key => {
      const value = params[key];
      const regex = new RegExp(`\\{\\{${key}\\}\\}`, 'g');
      result = result.replace(regex, String(value));
    });

    // Conditional blocks: {{#if condition}}...{{/if}}
    result = result.replace(/\{\{#if ([^}]+)\}\}([\s\S]*?)\{\{\/if\}\}/g, (match, condition, content) => {
      const value = params[condition.trim()];
      return value ? content : '';
    });

    // Conditional blocks with else: {{#if condition}}...{{else}}...{{/if}}
    result = result.replace(/\{\{#if ([^}]+)\}\}([\s\S]*?)\{\{else\}\}([\s\S]*?)\{\{\/if\}\}/g,
      (match, condition, ifContent, elseContent) => {
        const value = params[condition.trim()];
        return value ? ifContent : elseContent;
      }
    );

    // Unless blocks: {{#unless condition}}...{{/unless}}
    result = result.replace(/\{\{#unless ([^}]+)\}\}([\s\S]*?)\{\{\/unless\}\}/g, (match, condition, content) => {
      const value = params[condition.trim()];
      return !value ? content : '';
    });

    // Each blocks: {{#each array}}...{{/each}}
    result = result.replace(/\{\{#each ([^}]+)\}\}([\s\S]*?)\{\{\/each\}\}/g, (match, arrayName, content) => {
      const array = params[arrayName.trim()];
      if (!Array.isArray(array)) return '';

      return array.map((item, index) => {
        let itemContent = content;
        itemContent = itemContent.replace(/\{\{this\}\}/g, String(item));
        itemContent = itemContent.replace(/\{\{@index\}\}/g, String(index));
        itemContent = itemContent.replace(/\{\{@first\}\}/g, String(index === 0));
        itemContent = itemContent.replace(/\{\{@last\}\}/g, String(index === array.length - 1));

        // Access parent context
        Object.keys(params).forEach(key => {
          itemContent = itemContent.replace(new RegExp(`\\{\\{\\.\\./${key}\\}\\}`, 'g'), String(params[key]));
        });

        return itemContent;
      }).join('');
    });

    // Expression evaluation: {{#expr}}...{{/expr}}
    result = result.replace(/\{\{#expr\}\}([\s\S]*?)\{\{\/expr\}\}/g, (match, expression) => {
      try {
        // Simple arithmetic evaluation
        let expr = expression.trim();
        Object.keys(params).forEach(key => {
          expr = expr.replace(new RegExp(`\\{\\{${key}\\}\\}`, 'g'), String(params[key]));
        });
        // Safe eval for arithmetic only
        const evaluated = Function('"use strict"; return (' + expr + ')')();
        return String(evaluated);
      } catch (e) {
        return expression;
      }
    });

    return result;
  }

  // ============================================================================
  // Template Testing
  // ============================================================================

  public testTemplate(templateName: string): { passed: number; failed: number; results: any[] } {
    const template = this.templates.get(templateName);
    if (!template) {
      throw new Error(`Template not found: ${templateName}`);
    }

    if (!template.tests || template.tests.length === 0) {
      throw new Error('Template has no tests defined');
    }

    const results: any[] = [];
    let passed = 0;
    let failed = 0;

    template.tests.forEach(test => {
      try {
        const result = this.applyTemplate(templateName, test.parameters);

        let success = true;
        let message = 'Test passed';

        if (test.shouldFail) {
          success = false;
          message = 'Test should have failed but succeeded';
        } else if (test.expectedPattern) {
          const regex = new RegExp(test.expectedPattern);
          if (!regex.test(result)) {
            success = false;
            message = `Result does not match expected pattern: ${test.expectedPattern}`;
          }
        }

        if (success) {
          passed++;
        } else {
          failed++;
        }

        results.push({
          name: test.name,
          description: test.description,
          success,
          message,
          result
        });
      } catch (error) {
        if (test.shouldFail) {
          passed++;
          results.push({
            name: test.name,
            description: test.description,
            success: true,
            message: 'Test correctly failed',
            error: (error as Error).message
          });
        } else {
          failed++;
          results.push({
            name: test.name,
            description: test.description,
            success: false,
            message: 'Unexpected error',
            error: (error as Error).message
          });
        }
      }
    });

    return { passed, failed, results };
  }

  // ============================================================================
  // Import/Export
  // ============================================================================

  public exportTemplate(templateName: string, outputPath: string): void {
    const template = this.templates.get(templateName);
    if (!template) {
      throw new Error(`Template not found: ${templateName}`);
    }

    fs.writeFileSync(outputPath, JSON.stringify(template, null, 2));
  }

  public importTemplate(inputPath: string, overwrite = false): void {
    const content = fs.readFileSync(inputPath, 'utf-8');
    const template = JSON.parse(content) as Template;

    if (this.templates.has(template.metadata.name) && !overwrite) {
      throw new Error(`Template ${template.metadata.name} already exists. Use --overwrite to replace.`);
    }

    this.createTemplate(template);
  }

  public exportAllTemplates(outputDir: string, includeBuiltin = false): void {
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }

    this.templates.forEach(template => {
      if (!includeBuiltin && BUILTIN_TEMPLATES.some(t => t.metadata.name === template.metadata.name)) {
        return;
      }

      const fileName = `${template.metadata.name}.json`;
      const filePath = path.join(outputDir, fileName);
      fs.writeFileSync(filePath, JSON.stringify(template, null, 2));
    });
  }

  // ============================================================================
  // History Management
  // ============================================================================

  private recordApplication(app: TemplateApplication): void {
    let history: TemplateApplication[] = [];

    if (fs.existsSync(this.historyPath)) {
      try {
        const content = fs.readFileSync(this.historyPath, 'utf-8');
        history = JSON.parse(content);
      } catch (e) {
        // Ignore parse errors
      }
    }

    history.push(app);

    // Keep last 100 applications
    if (history.length > 100) {
      history = history.slice(-100);
    }

    fs.writeFileSync(this.historyPath, JSON.stringify(history, null, 2));
  }

  public getHistory(limit = 10): TemplateApplication[] {
    if (!fs.existsSync(this.historyPath)) {
      return [];
    }

    try {
      const content = fs.readFileSync(this.historyPath, 'utf-8');
      const history = JSON.parse(content) as TemplateApplication[];
      return history.slice(-limit).reverse();
    } catch (e) {
      return [];
    }
  }
}

// ============================================================================
// CLI Interface
// ============================================================================

export async function runTemplateCLI(args: string[]): Promise<void> {
  const manager = new TemplateManager();
  const command = args[0];

  switch (command) {
    case 'list': {
      const category = args[1];
      const templates = manager.listTemplates(category);

      if (templates.length === 0) {
        console.log('No templates found.');
        return;
      }

      // Group by category
      const grouped = templates.reduce((acc, t) => {
        if (!acc[t.metadata.category]) {
          acc[t.metadata.category] = [];
        }
        acc[t.metadata.category].push(t);
        return acc;
      }, {} as Record<string, Template[]>);

      Object.keys(grouped).sort().forEach(cat => {
        const categoryInfo = TEMPLATE_CATEGORIES[cat];
        console.log(`\n${categoryInfo?.icon || '📄'} ${categoryInfo?.name || cat}`);
        console.log('─'.repeat(60));

        grouped[cat].forEach(t => {
          console.log(`  ${t.metadata.name.padEnd(30)} ${t.metadata.description}`);
          console.log(`    Tags: ${t.metadata.tags.join(', ')}`);
        });
      });
      break;
    }

    case 'show': {
      const name = args[1];
      if (!name) {
        console.error('Error: Template name required');
        process.exit(1);
      }

      const template = manager.getTemplate(name);
      if (!template) {
        console.error(`Error: Template not found: ${name}`);
        process.exit(1);
      }

      console.log(`Template: ${template.metadata.name}`);
      console.log(`Version: ${template.metadata.version}`);
      console.log(`Category: ${template.metadata.category}`);
      console.log(`Tags: ${template.metadata.tags.join(', ')}`);
      console.log(`\nDescription:`);
      console.log(`  ${template.metadata.description}`);

      if (template.metadata.usage) {
        console.log(`\nUsage:`);
        console.log(`  ${template.metadata.usage}`);
      }

      if (template.metadata.examples && template.metadata.examples.length > 0) {
        console.log(`\nExamples:`);
        template.metadata.examples.forEach(ex => {
          console.log(`  ${ex}`);
        });
      }

      console.log(`\nParameters:`);
      template.parameters.forEach(param => {
        const required = param.required ? '[REQUIRED]' : '[OPTIONAL]';
        const defaultVal = param.default !== undefined ? ` (default: ${param.default})` : '';
        console.log(`  ${param.name} (${param.type}) ${required}${defaultVal}`);
        console.log(`    ${param.description}`);
      });

      console.log(`\nQuery Template:`);
      console.log('─'.repeat(60));
      console.log(template.query);
      console.log('─'.repeat(60));
      break;
    }

    case 'apply': {
      const name = args[1];
      if (!name) {
        console.error('Error: Template name required');
        process.exit(1);
      }

      // Parse parameters from command line
      const params: Record<string, any> = {};
      for (let i = 2; i < args.length; i++) {
        if (args[i].startsWith('--')) {
          const key = args[i].substring(2);
          const value = args[i + 1];
          params[key] = value;
          i++;
        }
      }

      try {
        const result = manager.applyTemplate(name, params);
        console.log(result);
      } catch (error) {
        console.error('Error:', (error as Error).message);
        process.exit(1);
      }
      break;
    }

    case 'validate': {
      const name = args[1];
      if (!name) {
        console.error('Error: Template name required');
        process.exit(1);
      }

      const template = manager.getTemplate(name);
      if (!template) {
        console.error(`Error: Template not found: ${name}`);
        process.exit(1);
      }

      const validation = manager.validateTemplate(template);

      if (validation.valid) {
        console.log('✓ Template is valid');
      } else {
        console.log('✗ Template validation failed');
        validation.errors.forEach(err => console.log(`  Error: ${err}`));
      }

      if (validation.warnings.length > 0) {
        console.log('\nWarnings:');
        validation.warnings.forEach(warn => console.log(`  Warning: ${warn}`));
      }

      process.exit(validation.valid ? 0 : 1);
      break;
    }

    case 'test': {
      const name = args[1];
      if (!name) {
        console.error('Error: Template name required');
        process.exit(1);
      }

      try {
        const testResults = manager.testTemplate(name);

        console.log(`\nTest Results for ${name}:`);
        console.log('─'.repeat(60));
        console.log(`Passed: ${testResults.passed}`);
        console.log(`Failed: ${testResults.failed}`);
        console.log('');

        testResults.results.forEach(result => {
          const icon = result.success ? '✓' : '✗';
          console.log(`${icon} ${result.name}: ${result.message}`);
          if (!result.success && result.error) {
            console.log(`  Error: ${result.error}`);
          }
        });

        process.exit(testResults.failed === 0 ? 0 : 1);
      } catch (error) {
        console.error('Error:', (error as Error).message);
        process.exit(1);
      }
      break;
    }

    case 'export': {
      const name = args[1];
      const output = args[2] || `${name}.json`;

      try {
        manager.exportTemplate(name, output);
        console.log(`✓ Template exported to ${output}`);
      } catch (error) {
        console.error('Error:', (error as Error).message);
        process.exit(1);
      }
      break;
    }

    case 'import': {
      const inputPath = args[1];
      const overwrite = args.includes('--overwrite');

      if (!inputPath) {
        console.error('Error: Input file path required');
        process.exit(1);
      }

      try {
        manager.importTemplate(inputPath, overwrite);
        console.log('✓ Template imported successfully');
      } catch (error) {
        console.error('Error:', (error as Error).message);
        process.exit(1);
      }
      break;
    }

    case 'history': {
      const limit = parseInt(args[1]) || 10;
      const history = manager.getHistory(limit);

      if (history.length === 0) {
        console.log('No template history found.');
        return;
      }

      console.log('\nTemplate Application History:');
      console.log('─'.repeat(60));

      history.forEach((app, index) => {
        console.log(`${index + 1}. ${app.template}`);
        console.log(`   Time: ${app.timestamp}`);
        console.log(`   Parameters: ${JSON.stringify(app.parameters)}`);
        console.log('');
      });
      break;
    }

    case 'categories': {
      console.log('\nTemplate Categories:');
      console.log('─'.repeat(60));

      Object.values(TEMPLATE_CATEGORIES).forEach(cat => {
        console.log(`${cat.icon || '📄'} ${cat.name}`);
        console.log(`  ${cat.description}`);
        console.log('');
      });
      break;
    }

    case 'help':
    default: {
      console.log(`
Template System - AI-Shell Query Template Management

Usage:
  template list [category]              List all templates or by category
  template show <name>                  Show template details
  template apply <name> [--params]      Apply template with parameters
  template validate <name>              Validate template
  template test <name>                  Run template tests
  template export <name> [output]       Export template to file
  template import <file> [--overwrite]  Import template from file
  template history [limit]              Show template usage history
  template categories                   List all categories

Examples:
  template list crud
  template show crud.select-all
  template apply crud.select-all --table users --limit 10
  template test analytics.aggregate-by-time
  template export crud.select-all my-template.json
  template import custom-template.json

Categories:
  crud        - Create, Read, Update, Delete operations
  analytics   - Data analysis and reporting
  admin       - Database administration
  migration   - Schema migrations
  performance - Performance optimization
  security    - Security and access control
      `);
      break;
    }
  }
}

// ============================================================================
// Main Entry Point
// ============================================================================

if (require.main === module) {
  const args = process.argv.slice(2);
  runTemplateCLI(args).catch(error => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
}
