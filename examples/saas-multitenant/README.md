# SaaS Multi-Tenant Application - AI-Shell Example

## Scenario: Multi-Tenant SaaS with Complete Isolation

This example demonstrates managing a multi-tenant SaaS application where each customer (tenant) has isolated data, custom configurations, and independent performance tuning. Perfect for B2B SaaS platforms requiring strict data isolation and per-tenant analytics.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  AI-Shell Multi-Tenant Manager                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              PostgreSQL - Schema-per-Tenant               │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐    │   │
│  │  │ tenant_1│  │ tenant_2│  │ tenant_3│  │   ...   │    │   │
│  │  │ (Acme)  │  │(TechCo) │  │(StartUp)│  │         │    │   │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘    │   │
│  │                                                           │   │
│  │              + Master Schema (tenant metadata)            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │         MongoDB - Cross-Tenant Analytics DB              │   │
│  │  - Aggregated metrics    - Usage tracking                │   │
│  │  - Billing data          - Audit logs                    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Redis - Per-Tenant Caching                  │   │
│  │  - Session management    - Rate limiting                 │   │
│  │  - Feature flags         - Cache by tenant               │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Key Features

- **Schema-per-Tenant**: Complete data isolation with dedicated PostgreSQL schemas
- **Automated Provisioning**: New tenant setup in seconds with AI-Shell
- **Cross-Tenant Analytics**: Aggregate insights without breaking isolation
- **Per-Tenant Optimization**: Independent query tuning and indexing
- **Cost Tracking**: Monitor and bill based on actual resource usage
- **Compliance Ready**: GDPR, SOC2, HIPAA data isolation
- **Intelligent Routing**: Automatic tenant identification and routing
- **Migration Tools**: Move tenants between databases for scaling

## Prerequisites

- Docker & Docker Compose
- AI-Shell installed
- 4GB RAM minimum
- Understanding of multi-tenancy patterns

## Quick Start

### 1. Setup Environment

```bash
cd examples/saas-multitenant
./scripts/setup.sh
```

This creates:
- 5 sample tenants with isolated schemas
- Master database for tenant management
- MongoDB for cross-tenant analytics
- Redis for tenant-aware caching

### 2. Run the Demo

```bash
./scripts/demo.sh
```

Demonstrates:
- Tenant provisioning and de-provisioning
- Cross-tenant analytics
- Per-tenant query optimization
- Cost tracking and billing
- Migration scenarios

### 3. Interactive Usage

```bash
ai-shell

# Tenant management
"Create a new tenant called 'BigCorp' with premium plan"
"Show me all tenants and their resource usage"
"Migrate tenant 'Acme' to a dedicated database instance"

# Per-tenant queries
"Show users for tenant 'Acme'"
"What's the average response time for tenant 'TechCo' queries?"
"Find slow queries specific to tenant 'StartUp'"

# Cross-tenant analytics
"Compare monthly active users across all tenants"
"Which tenants are approaching their plan limits?"
"Show revenue by tenant tier (free, pro, enterprise)"
