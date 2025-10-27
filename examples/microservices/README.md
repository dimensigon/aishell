# Microservices Data Mesh - AI-Shell Example

## Scenario: Distributed Microservices with Independent Databases

This example demonstrates managing a microservices architecture where each service owns its database, following the database-per-service pattern. Shows how AI-Shell can query across service boundaries while maintaining service independence.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│              AI-Shell Microservices Coordinator                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │  Users   │  │ Products │  │  Orders  │  │ Payments │       │
│  │ Service  │  │ Service  │  │ Service  │  │ Service  │       │
│  │          │  │          │  │          │  │          │       │
│  │ Postgres │  │  MySQL   │  │ Postgres │  │  Mongo   │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
│                                                                   │
│  ┌──────────┐  ┌──────────┐                                    │
│  │Analytics │  │  Notif.  │                                    │
│  │ Service  │  │ Service  │                                    │
│  │          │  │          │                                    │
│  │Clickhouse│  │  Redis   │                                    │
│  └──────────┘  └──────────┘                                    │
│                                                                   │
│  ┌───────────────────────────────────────────────────────┐     │
│  │            Event Bus (Kafka/RabbitMQ)                 │     │
│  │  - Service events    - Data changes                   │     │
│  │  - Cross-service sync - Audit trail                   │     │
│  └───────────────────────────────────────────────────────┘     │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Key Features

- **Database-per-Service**: Each microservice owns its data
- **Cross-Service Queries**: Federation without tight coupling
- **Schema Evolution**: Independent versioning per service
- **Polyglot Persistence**: Different databases for different needs
- **Event-Driven Sync**: Eventual consistency via events
- **API Composition**: Aggregate data from multiple services
- **Multi-Cloud**: Services across AWS and GCP

## Services

1. **User Service** (PostgreSQL) - Authentication, profiles
2. **Product Service** (MySQL) - Catalog, inventory
3. **Order Service** (PostgreSQL) - Order processing
4. **Payment Service** (MongoDB) - Transactions, billing
5. **Analytics Service** (ClickHouse) - Metrics, reporting
6. **Notification Service** (Redis) - Alerts, messaging

## Quick Start

```bash
cd examples/microservices
./scripts/setup.sh
./scripts/demo.sh
```

## Example Queries

```
"Show complete order details with user and product info across services"
"Find payment failures and correlate with user service health"
"Compare schema differences between services"
"Track an event across all microservices"
"Generate cross-service analytics report"
```

[Full Documentation →](./README.md)
