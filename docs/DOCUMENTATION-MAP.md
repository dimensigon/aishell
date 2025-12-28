# AI-Shell Documentation Map

**Visual Guide to Documentation Structure**
**Version:** 2.0 (Proposed Reorganization)
**Date:** October 30, 2025

---

## Quick Navigation

**I want to...**

| Goal | Start Here |
|------|-----------|
| Get started in 5 minutes | [Quickstart Guide](getting-started/quickstart.md) |
| Install AI-Shell | [Installation Guide](getting-started/installation.md) |
| Look up a command | [CLI Commands Reference](reference/cli/commands.md) |
| Connect to PostgreSQL | [PostgreSQL Guide](guides/databases/postgresql.md) |
| Optimize a slow query | [Performance Tuning](guides/operations/performance-tuning.md) |
| Set up backups | [Backup & Recovery](guides/operations/backup-recovery.md) |
| Understand the architecture | [Architecture Overview](concepts/architecture/overview.md) |
| Deploy to production | [Production Checklist](deployment/production-checklist.md) |
| Contribute code | [Contributing Guide](contributing/README.md) |
| Troubleshoot an issue | [Troubleshooting](guides/operations/troubleshooting.md) |

---

## Complete Documentation Tree

```
📚 AI-Shell Documentation
│
├── 📖 README.md ⭐ START HERE
│   └── Main navigation hub with quick links
│
├── 🚀 getting-started/          [TUTORIALS - Learning Oriented]
│   ├── README.md                 Navigation for beginners
│   ├── quickstart.md             5-minute setup guide
│   ├── installation.md           Detailed installation
│   ├── configuration.md          Initial configuration
│   └── first-steps.md            Your first commands
│
├── 📚 guides/                   [HOW-TO GUIDES - Task Oriented]
│   ├── README.md                 Guide navigation
│   │
│   ├── databases/                Database-specific operations
│   │   ├── postgresql.md         PostgreSQL operations
│   │   ├── mysql.md              MySQL operations
│   │   ├── mongodb.md            MongoDB operations
│   │   └── redis.md              Redis operations
│   │
│   ├── security/                 Security and compliance
│   │   ├── vault-setup.md        Credential management
│   │   ├── audit-logging.md      Security auditing
│   │   └── compliance.md         GDPR, HIPAA, PCI-DSS, SOC 2
│   │
│   ├── operations/               Day-to-day operations
│   │   ├── backup-recovery.md    Backup strategies
│   │   ├── monitoring.md         Health monitoring
│   │   ├── performance-tuning.md Query optimization
│   │   └── troubleshooting.md    Problem solving
│   │
│   └── integrations/             Third-party integrations
│       ├── slack.md              Slack integration
│       ├── grafana.md            Grafana dashboards
│       ├── prometheus.md         Prometheus metrics
│       └── cicd.md               CI/CD pipelines
│
├── 📋 reference/                [REFERENCE - Information Oriented]
│   ├── README.md                 Reference navigation
│   │
│   ├── cli/                      Command-line interface
│   │   ├── commands.md           All 106 CLI commands
│   │   ├── options.md            Global options and flags
│   │   └── configuration.md      Config file reference
│   │
│   ├── api/                      Programmatic APIs
│   │   ├── typescript-api.md     TypeScript API
│   │   ├── python-api.md         Python bindings (future)
│   │   └── rest-api.md           REST API (MCP servers)
│   │
│   └── configuration/            Configuration reference
│       ├── environment-variables.md  All environment variables
│       ├── config-file-schema.md     YAML/JSON schema
│       └── defaults.md               Default values
│
├── 💡 concepts/                 [EXPLANATION - Understanding Oriented]
│   ├── README.md                 Concepts navigation
│   │
│   ├── architecture/             System architecture
│   │   ├── overview.md           System architecture
│   │   ├── database-adapters.md  Adapter pattern
│   │   ├── ai-integration.md     AI/LLM integration
│   │   └── security-model.md     Security design
│   │
│   ├── features/                 Feature deep-dives
│   │   ├── natural-language.md   NL query processing
│   │   ├── query-optimization.md AI optimization
│   │   ├── federation.md         Multi-DB queries
│   │   └── autonomous-agents.md  ADA agent system
│   │
│   └── design-decisions/         Design philosophy
│       ├── database-support.md   Why these databases?
│       ├── llm-choice.md         Claude vs alternatives
│       └── cli-design.md         CLI design philosophy
│
├── 🎓 tutorials/                [STEP-BY-STEP - Project Based]
│   ├── README.md                 Tutorials navigation
│   │
│   ├── beginner/                 Start from scratch
│   │   ├── 01-first-connection.md    Connect to database
│   │   ├── 02-basic-queries.md       Run your first queries
│   │   ├── 03-health-monitoring.md   Set up monitoring
│   │   └── 04-secure-credentials.md  Use vault for passwords
│   │
│   ├── intermediate/             Level up your skills
│   │   ├── 01-query-optimization.md  Optimize slow queries
│   │   ├── 02-automated-backups.md   Schedule backups
│   │   ├── 03-alerting.md            Configure alerts
│   │   └── 04-multi-database.md      Work with multiple DBs
│   │
│   └── advanced/                 Master AI-Shell
│       ├── 01-database-federation.md  Cross-DB queries
│       ├── 02-custom-agents.md        Build custom AI agents
│       ├── 03-enterprise-deploy.md    Production deployment
│       └── 04-performance-at-scale.md Scale optimization
│
├── 🚢 deployment/               [DEPLOYMENT - Operations Oriented]
│   ├── README.md                 Deployment navigation
│   ├── production-checklist.md  Pre-deployment checklist
│   │
│   ├── installation/             Installation methods
│   │   ├── docker.md             Docker deployment
│   │   ├── kubernetes.md         Kubernetes deployment
│   │   └── bare-metal.md         Traditional install
│   │
│   ├── configuration/            Production configuration
│   │   ├── production-config.md  Production settings
│   │   ├── security-hardening.md Security configuration
│   │   └── high-availability.md  HA setup
│   │
│   └── monitoring/               Production monitoring
│       ├── setup.md              Monitoring setup
│       ├── alerts.md             Alert configuration
│       └── dashboards.md         Dashboard templates
│
├── 🤝 contributing/             [DEVELOPER - Contributor Oriented]
│   ├── README.md                 Contributor navigation
│   ├── getting-started.md        Dev environment setup
│   ├── code-style.md             Coding standards
│   ├── testing.md                Testing guidelines
│   ├── documentation.md          Doc contribution guide
│   └── architecture.md           Architecture for devs
│
├── 📦 archive/                  [LEGACY - Deprecated Content]
│   ├── README.md                 What's archived and why
│   ├── phase-reports/            Historical phase reports
│   ├── old-architecture/         Superseded architecture
│   └── status-reports/           Historical status
│
└── 🔒 internal/                 [INTERNAL - Project Management]
    ├── reports/                  Technical reports
    ├── research/                 Research documents
    ├── planning/                 Sprint planning
    └── presentations/            Stakeholder presentations
```

---

## Documentation Categories Explained

### 🚀 Getting Started (Tutorials)

**Purpose:** Help you learn the basics
**Audience:** New users, beginners
**Format:** Step-by-step learning guides
**Time commitment:** 5 minutes to 1 hour

**When to use:**
- You're new to AI-Shell
- You want a quick overview
- You need basic concepts explained
- You want to try it out quickly

**Example docs:**
- Quickstart (5 minutes)
- Installation guide
- First steps tutorial

---

### 📚 Guides (How-To)

**Purpose:** Solve specific problems
**Audience:** All users with a specific task
**Format:** Task-oriented instructions
**Time commitment:** 10-30 minutes per guide

**When to use:**
- You need to accomplish a specific task
- You know what you want to do
- You want best practices
- You need step-by-step instructions

**Example docs:**
- How to connect to PostgreSQL
- How to optimize a slow query
- How to set up automated backups

---

### 📋 Reference (Information)

**Purpose:** Look up facts and details
**Audience:** Users who know what they're looking for
**Format:** Structured reference material
**Time commitment:** 1-5 minutes (quick lookup)

**When to use:**
- You need command syntax
- You want to look up an API method
- You need configuration options
- You're checking default values

**Example docs:**
- CLI command reference
- API documentation
- Configuration schema

---

### 💡 Concepts (Explanation)

**Purpose:** Understand how and why
**Audience:** Users wanting deep understanding
**Format:** Explanatory content
**Time commitment:** 15-45 minutes per topic

**When to use:**
- You want to understand the "why"
- You need architectural knowledge
- You're curious about design decisions
- You want to become an expert

**Example docs:**
- Architecture overview
- How natural language processing works
- Why we chose this database adapter pattern

---

### 🎓 Tutorials (Step-by-Step)

**Purpose:** Complete projects from start to finish
**Audience:** Learners at different levels
**Format:** Complete project walkthroughs
**Time commitment:** 30 minutes to 2 hours

**When to use:**
- You want to build something complete
- You learn best by doing
- You want a guided project
- You want to see real-world examples

**Example docs:**
- Beginner: Set up your first database connection
- Intermediate: Build an automated backup system
- Advanced: Deploy database federation at scale

---

### 🚢 Deployment (Operations)

**Purpose:** Deploy and operate in production
**Audience:** DevOps, SREs, operators
**Format:** Operational guides and checklists
**Time commitment:** Varies (setup to ongoing)

**When to use:**
- You're deploying to production
- You need operational procedures
- You want to ensure high availability
- You need monitoring setup

**Example docs:**
- Production deployment checklist
- Kubernetes deployment guide
- Monitoring setup

---

### 🤝 Contributing (Developer)

**Purpose:** Contribute to the project
**Audience:** Contributors, developers
**Format:** Development guides and standards
**Time commitment:** Varies

**When to use:**
- You want to contribute code
- You want to report a bug properly
- You need to set up dev environment
- You want to understand codebase

**Example docs:**
- Getting started as a contributor
- Code style guide
- Testing guidelines

---

## User Journey Maps

### Journey 1: Complete Beginner

```
START: Never used AI-Shell before
│
├─→ docs/README.md (Main hub)
│   └─→ "New to AI-Shell?" section
│
├─→ getting-started/quickstart.md (5 min)
│   └─→ First query in 5 minutes
│
├─→ getting-started/first-steps.md (15 min)
│   └─→ Learn basic commands
│
├─→ tutorials/beginner/01-first-connection.md (30 min)
│   └─→ Complete first project
│
└─→ guides/databases/postgresql.md (as needed)
    └─→ Solve specific problems

OUTCOME: Productive with AI-Shell in 1 hour
```

---

### Journey 2: Database Administrator

```
START: Need to monitor production database
│
├─→ docs/README.md
│   └─→ "Guides (How-To)" section
│
├─→ guides/operations/monitoring.md
│   └─→ Set up health monitoring
│
├─→ guides/integrations/grafana.md
│   └─→ Create dashboards
│
├─→ reference/cli/commands.md
│   └─→ Look up specific commands
│
└─→ deployment/monitoring/setup.md
    └─→ Production monitoring

OUTCOME: Production monitoring in 2 hours
```

---

### Journey 3: Developer

```
START: Want to integrate AI-Shell into my app
│
├─→ docs/README.md
│   └─→ "Reference" section
│
├─→ reference/api/typescript-api.md
│   └─→ Learn the API
│
├─→ concepts/architecture/overview.md
│   └─→ Understand architecture
│
├─→ tutorials/advanced/02-custom-agents.md
│   └─→ Build custom integration
│
└─→ contributing/README.md
    └─→ Contribute improvements

OUTCOME: Custom integration built in 4 hours
```

---

### Journey 4: Enterprise Architect

```
START: Evaluating AI-Shell for enterprise
│
├─→ docs/README.md
│   └─→ "Concepts" section
│
├─→ concepts/architecture/overview.md
│   └─→ Understand system design
│
├─→ concepts/architecture/security-model.md
│   └─→ Evaluate security
│
├─→ guides/security/compliance.md
│   └─→ Check compliance features
│
├─→ deployment/production-checklist.md
│   └─→ Plan deployment
│
└─→ tutorials/advanced/03-enterprise-deploy.md
    └─→ POC deployment

OUTCOME: Enterprise evaluation complete in 1 day
```

---

## Cross-Reference Map

### Database Guides Cross-References

```
guides/databases/postgresql.md
├─→ Related Concepts
│   └─→ concepts/architecture/database-adapters.md
├─→ Related Guides
│   ├─→ guides/operations/performance-tuning.md
│   └─→ guides/operations/backup-recovery.md
├─→ Related Reference
│   └─→ reference/cli/commands.md (PostgreSQL commands)
└─→ Related Tutorials
    └─→ tutorials/beginner/01-first-connection.md
```

### Security Guides Cross-References

```
guides/security/vault-setup.md
├─→ Related Concepts
│   └─→ concepts/architecture/security-model.md
├─→ Related Guides
│   ├─→ guides/security/audit-logging.md
│   └─→ guides/security/compliance.md
├─→ Related Reference
│   └─→ reference/cli/commands.md (security commands)
└─→ Related Tutorials
    └─→ tutorials/beginner/04-secure-credentials.md
```

### Performance Guides Cross-References

```
guides/operations/performance-tuning.md
├─→ Related Concepts
│   └─→ concepts/features/query-optimization.md
├─→ Related Guides
│   ├─→ guides/databases/postgresql.md
│   └─→ guides/operations/monitoring.md
├─→ Related Reference
│   └─→ reference/cli/commands.md (optimization commands)
└─→ Related Tutorials
    └─→ tutorials/intermediate/01-query-optimization.md
```

---

## Search & Discovery

### By Feature

| Feature | Reference | Guide | Concept | Tutorial |
|---------|-----------|-------|---------|----------|
| **Natural Language Queries** | [Commands](reference/cli/commands.md#translate) | [Using NL](guides/databases/postgresql.md#natural-language) | [How NL Works](concepts/features/natural-language.md) | [Basic Queries](tutorials/beginner/02-basic-queries.md) |
| **Query Optimization** | [Commands](reference/cli/commands.md#optimize) | [Performance Tuning](guides/operations/performance-tuning.md) | [Optimization Concepts](concepts/features/query-optimization.md) | [Optimization Tutorial](tutorials/intermediate/01-query-optimization.md) |
| **Backup & Recovery** | [Commands](reference/cli/commands.md#backup) | [Backup Guide](guides/operations/backup-recovery.md) | - | [Backup Tutorial](tutorials/intermediate/02-automated-backups.md) |
| **Database Federation** | [Commands](reference/cli/commands.md#federation) | - | [Federation Concepts](concepts/features/federation.md) | [Federation Tutorial](tutorials/advanced/01-database-federation.md) |
| **Security** | [Commands](reference/cli/commands.md#vault) | [Security Guides](guides/security/) | [Security Model](concepts/architecture/security-model.md) | [Security Tutorial](tutorials/beginner/04-secure-credentials.md) |

### By Database

| Database | Guide | Tutorial | Reference |
|----------|-------|----------|-----------|
| **PostgreSQL** | [PG Guide](guides/databases/postgresql.md) | [PG Tutorial](tutorials/beginner/01-first-connection.md) | [PG Commands](reference/cli/commands.md#postgresql) |
| **MySQL** | [MySQL Guide](guides/databases/mysql.md) | [MySQL Tutorial](tutorials/beginner/01-first-connection.md) | [MySQL Commands](reference/cli/commands.md#mysql) |
| **MongoDB** | [Mongo Guide](guides/databases/mongodb.md) | [Mongo Tutorial](tutorials/beginner/01-first-connection.md) | [Mongo Commands](reference/cli/commands.md#mongodb) |
| **Redis** | [Redis Guide](guides/databases/redis.md) | [Redis Tutorial](tutorials/beginner/01-first-connection.md) | [Redis Commands](reference/cli/commands.md#redis) |

### By User Role

| Role | Start Here | Key Docs |
|------|-----------|----------|
| **New User** | [Quickstart](getting-started/quickstart.md) | Getting Started, Beginner Tutorials |
| **Database Admin** | [Operations Guides](guides/operations/) | Database Guides, Monitoring, Backup |
| **Developer** | [API Reference](reference/api/) | Concepts, Advanced Tutorials |
| **DevOps Engineer** | [Deployment](deployment/) | Production Checklist, Monitoring Setup |
| **Security Engineer** | [Security Guides](guides/security/) | Compliance, Security Model |
| **Contributor** | [Contributing](contributing/) | Dev Setup, Code Style, Testing |

---

## Documentation Statistics

### By Category

| Category | Files | Purpose | Audience |
|----------|-------|---------|----------|
| Getting Started | 4 | Learn basics | Beginners |
| Guides | 15 | Solve problems | All users |
| Reference | 8 | Look up facts | All users |
| Concepts | 12 | Understand deeply | Advanced users |
| Tutorials | 12 | Complete projects | Learners |
| Deployment | 9 | Deploy/operate | DevOps |
| Contributing | 6 | Contribute | Developers |
| **Total User Docs** | **66** | | |
| Archive | ~100 | Historical | Internal |
| Internal | ~150 | Project mgmt | Team |
| **Total Docs** | **~316** | | |

### Reduction from Current

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Total files | 414 | ~316 | 24% reduction |
| User-facing | ~250 | 66 | 74% reduction |
| Duplicate content | ~30% | <5% | 25% improvement |
| Navigation depth | 3-4 clicks | 2-3 clicks | 25-33% improvement |

---

## Quick Reference: Find What You Need

### "I want to..."

| Task | Document |
|------|----------|
| **Install AI-Shell** | [Installation](getting-started/installation.md) |
| **Connect to my database** | [First Connection](tutorials/beginner/01-first-connection.md) |
| **Run a query in plain English** | [Basic Queries](tutorials/beginner/02-basic-queries.md) |
| **Look up a command** | [CLI Commands](reference/cli/commands.md) |
| **Optimize a slow query** | [Performance Tuning](guides/operations/performance-tuning.md) |
| **Set up automated backups** | [Backup Guide](guides/operations/backup-recovery.md) |
| **Monitor database health** | [Monitoring](guides/operations/monitoring.md) |
| **Secure my credentials** | [Vault Setup](guides/security/vault-setup.md) |
| **Integrate with Slack** | [Slack Integration](guides/integrations/slack.md) |
| **Deploy to production** | [Production Checklist](deployment/production-checklist.md) |
| **Understand the architecture** | [Architecture Overview](concepts/architecture/overview.md) |
| **Build a custom agent** | [Custom Agents](tutorials/advanced/02-custom-agents.md) |
| **Contribute code** | [Contributing Guide](contributing/README.md) |
| **Troubleshoot an issue** | [Troubleshooting](guides/operations/troubleshooting.md) |

---

## Navigation Tips

### Best Practices

1. **Start at the top:** Always begin at [docs/README.md](README.md)
2. **Follow your role:** Use the "By User Role" table above
3. **Use search:** Ctrl+F to find keywords on this page
4. **Check cross-references:** Each doc links to related docs
5. **Bookmark favorites:** Save frequently-used docs

### Lost? Use This Decision Tree

```
Are you new to AI-Shell?
├─→ YES: Start with Getting Started
│   └─→ getting-started/quickstart.md
│
└─→ NO: What do you need?
    ├─→ Learn a concept → Tutorials or Concepts
    ├─→ Solve a problem → Guides
    ├─→ Look up a command → Reference
    ├─→ Deploy to prod → Deployment
    └─→ Contribute → Contributing
```

---

## Maintenance

**Last Updated:** October 30, 2025
**Next Review:** December 2025
**Maintained by:** Documentation Team

**How to update this map:**
1. Add new files to tree structure
2. Update statistics
3. Add to cross-reference map
4. Update user journeys if needed
5. Test all links
6. Update "Last Updated" date

---

## Feedback

**Documentation unclear?**
- Open an issue: [GitHub Issues](https://github.com/your-org/ai-shell/issues)
- Email: docs@ai-shell.dev
- Discord: #documentation channel

**Want to improve docs?**
- See [Contributing to Documentation](contributing/documentation.md)
- Submit a PR with improvements

---

**Ready to dive in?** Start with the [Main Documentation Hub](README.md)
