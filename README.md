# AIShell Consolidated

**Unified AIShell Implementation** - Multi-database AI-powered shell with cognitive features.

## Overview

AIShell Consolidated combines the best features from three AIShell implementations:
- **Base**: AIShell-Local (most complete, 158 files, 196 tests)
- **Enhanced**: Cognitive features from original AIShell
- **Extended**: Multi-database support (Oracle, PostgreSQL, MySQL)

## Key Features

### Core Features (from AIShell-Local)
- ✅ AI-powered SQL query generation
- ✅ Natural language database interactions
- ✅ MCP (Model Context Protocol) integration
- ✅ Safety and approval mechanisms
- ✅ Comprehensive test coverage (91.2%)
- ✅ TypeScript implementation
- ✅ LLM provider abstraction (Ollama, LlamaCpp)

### Cognitive Features (integrated from AIShell)
- 🧠 Pattern recognition and learning
- 🎯 Intelligent query optimization
- 💡 Context-aware recommendations
- 🔍 Vector search capabilities
- 📊 Usage pattern analysis

### Multi-Database Support (extended)
- 🗄️ Oracle Database (CDB$ROOT, FREEPDB1)
- 🐘 PostgreSQL (with JSONB, full-text search)
- 🐬 MySQL (with InnoDB, stored procedures)
- 🔄 Unified database abstraction layer
- 📈 Database-specific optimization

## Architecture

```
aishell-consolidated/
├── src/                    # Source code
│   ├── agents/            # AI agent implementations
│   ├── ai/                # AI/LLM integration
│   ├── api/               # API endpoints
│   ├── cli/               # Command-line interface
│   ├── cognitive/         # Cognitive features
│   ├── core/              # Core functionality
│   ├── database/          # Database adapters
│   ├── mcp/               # MCP protocol
│   └── utils/             # Utilities
├── tests/                 # Test suite
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   ├── e2e/              # End-to-end tests
│   └── database/         # Database-specific tests
├── config/               # Configuration
│   ├── environments/     # Environment configs
│   └── database/         # Database configs
├── docs/                 # Documentation
└── scripts/              # Utility scripts
```

## Quick Start

### Installation

```bash
# Install dependencies
npm install

# Build project
npm run build

# Run tests
npm test
```

### Database Setup

```bash
# Oracle Database
./scripts/database/setup-oracle.sh

# PostgreSQL
./scripts/database/setup-postgresql.sh

# MySQL
./scripts/database/setup-mysql.sh
```

### Configuration

1. Copy environment template:
```bash
cp .env.example .env
```

2. Configure database connections in `/config/database/`

3. Set environment variables:
```bash
export ORACLE_PASSWORD=your_password
export POSTGRES_PASSWORD=your_password
export MYSQL_PASSWORD=your_password
```

## Usage

### Basic Usage

```bash
# Start AIShell
npm start

# Connect to Oracle
aishell --db oracle --service freepdb1

# Connect to PostgreSQL
aishell --db postgresql

# Connect to MySQL
aishell --db mysql
```

### Natural Language Queries

```
> Show me all customers from New York
> Create a table for storing product information
> What's the average order value by region?
> Explain the query performance for my last search
```

## Testing

```bash
# Run all tests
npm test

# Run specific database tests
npm run test:oracle
npm run test:postgresql
npm run test:mysql

# Run with coverage
npm run test:coverage
```

## Database Environments

### Oracle Database
- **CDB$ROOT**: `localhost:1521/free`
- **FREEPDB1**: `localhost:1521/freepdb1`
- Test server: `51.15.90.27:1521`

### PostgreSQL
- **Local**: `localhost:5432/postgres`
- Test server: `51.15.90.27:5432`

### MySQL
- **Local**: `localhost:3307`
- Test server: `51.15.90.27:3307`

## Development

### Project Structure

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed architecture documentation.

### Contributing

1. Follow TypeScript best practices
2. Write tests for new features
3. Update documentation
4. Use conventional commit messages

### Code Standards

- ESLint configuration: `.eslintrc.json`
- Prettier configuration: `.prettierrc.json`
- TypeScript configuration: `tsconfig.json`

## Features Roadmap

### Phase 1: Foundation (Complete)
- ✅ Base implementation from AIShell-Local
- ✅ Multi-database configuration
- ✅ Test infrastructure

### Phase 2: Cognitive Integration (In Progress)
- 🔄 Pattern recognition system
- 🔄 Learning algorithms
- 🔄 Recommendation engine
- 🔄 Context management

### Phase 3: Database Extensions (Planned)
- ⏳ Oracle advanced features (RAC, ASM)
- ⏳ PostgreSQL extensions (PostGIS, TimescaleDB)
- ⏳ MySQL replication support
- ⏳ Cross-database queries

### Phase 4: Advanced Features (Planned)
- ⏳ Distributed query execution
- ⏳ Advanced security features
- ⏳ Performance monitoring
- ⏳ Cloud database support

## Documentation

- [Architecture Guide](docs/ARCHITECTURE.md)
- [API Documentation](docs/api/)
- [Database Guides](docs/guides/)
- [Tutorials](docs/tutorials/)

## License

MIT License - See LICENSE file for details

## Credits

Consolidated from:
- AIShell-Local (primary base)
- AIShell (cognitive features)
- aishell (documentation)

## Support

For issues and questions:
- GitHub Issues: [Create an issue]
- Documentation: [docs/](docs/)
- Tutorials: [docs/tutorials/](docs/tutorials/)
