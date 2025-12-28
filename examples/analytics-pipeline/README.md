# Analytics Dashboard - AI-Shell Example

## Scenario: Real-Time Analytics with Multiple Data Sources

This example demonstrates building a comprehensive analytics platform that aggregates data from multiple sources: transactional databases, event streams, logs, and search engines. Perfect for business intelligence, real-time dashboards, and data-driven decision making.

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                 AI-Shell Analytics Orchestrator                   │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐    │
│  │  PostgreSQL    │  │   ClickHouse   │  │  Elasticsearch │    │
│  │                │  │                │  │                │    │
│  │  - User Data   │  │  - Events      │  │  - Logs        │    │
│  │  - Metadata    │  │  - Metrics     │  │  - Full-text   │    │
│  │  - Relations   │  │  - Timeseries  │  │  - Search      │    │
│  └────────────────┘  └────────────────┘  └────────────────┘    │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    MongoDB                                │   │
│  │  - Unstructured events  - Session data                   │   │
│  │  - User behavior        - Analytics cache                │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                      Redis                                │   │
│  │  - Real-time counters   - Dashboard cache                │   │
│  │  - Leaderboards         - Session state                  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                    │
└──────────────────────────────────────────────────────────────────┘
```

## Key Features

- **Multi-Source Federation**: Query across SQL, NoSQL, and search databases
- **Real-Time Analytics**: Sub-second query response for dashboards
- **Time-Series Optimization**: ClickHouse for fast aggregations
- **Full-Text Search**: Elasticsearch for log analysis
- **Cache Strategy**: Multi-layer caching for performance
- **ETL Automation**: Scheduled data pipelines
- **Data Warehouse**: Optimized star schema design

## Quick Start

```bash
cd examples/analytics-pipeline
./scripts/setup.sh
./scripts/demo.sh
```

## Example Queries

```
"Show daily active users for the last 30 days"
"What's the conversion funnel from visit to purchase?"
"Find error spike patterns in the last week"
"Compare user engagement across different segments"
"Generate a cohort retention analysis"
```

## Sample Data

- 1M+ user events
- 100K users
- 50K sessions
- 500K log entries
- Real-time metrics

[Full Documentation →](./README.md)
