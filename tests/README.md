# AIShell Consolidated Test Suite

## Statistics
- **Total Files Before**: 601
- **Unique Files After**: 215
- **Duplicates Removed**: 386 (64.2% reduction)

## Structure
- unit/ - 176 files
- integration/ - 16 files
- e2e/ - 1 file
- functional/ - 2 files
- performance/ - 9 files
- security/ - 11 files

## Running Tests
```bash
# Python tests
pytest
pytest --cov=aishell

# TypeScript tests
npx vitest run
npx vitest --coverage
```

## Markers
- unit, integration, e2e
- performance, security, functional
- slow, database, ai, mcp
