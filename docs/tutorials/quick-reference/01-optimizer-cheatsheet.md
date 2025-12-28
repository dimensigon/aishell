# AI Query Optimizer - Quick Reference Card

## Essential Commands

```bash
# Analyze query performance
aishell optimize "your query here"

# Apply AI recommendations
aishell optimize "query" --apply

# Compare before/after
aishell optimize "query" --compare

# Auto-optimize slow queries
aishell optimize --watch --threshold 1000ms

# Test multiple strategies
aishell optimize --strategies "query"

# Rollback optimization
aishell optimize --rollback query-id
```

## Common Flags

| Flag | Description |
|------|-------------|
| `--apply` | Apply AI recommendations |
| `--compare` | Show before/after comparison |
| `--watch` | Monitor and auto-optimize |
| `--threshold <ms>` | Set slow query threshold |
| `--strategies` | Compare optimization approaches |
| `--rollback <id>` | Undo optimization |
| `--dry-run` | Preview changes without applying |
| `--balance read:write=80:20` | Balance read/write optimization |

## Typical Output

```
⚡ Execution Time: 45,231ms → 4.2ms (99.99% faster!)
💾 Rows Scanned: 1,000,000 → 142
📊 Memory Used: 2.4 GB → 12 KB
✅ Optimization Complete!
```

## Pro Tips

1. **Start with watch mode** for continuous optimization
2. **Use --dry-run first** to preview changes
3. **Enable caching** with `aishell cache enable`
4. **Monitor index overlap** with `aishell optimize --analyze-indexes`
5. **Test with production-like data** using `--clone-stats`

## When to Use

- ✅ Queries taking >1 second
- ✅ High CPU/memory usage
- ✅ Before major deployments
- ✅ After schema changes
- ✅ When adding new features

## Quick Wins

```bash
# Optimize top 10 slowest queries
aishell optimize --top 10 --apply

# Fix missing indexes
aishell optimize --fix-indexes

# Clean up redundant indexes
aishell optimize --cleanup-indexes
```

## Emergency Commands

```bash
# Query stuck? Kill it
aishell kill query-id

# Database overloaded? Stop writes
aishell emergency stop-writes

# Rollback bad optimization
aishell optimize --rollback --force
```

**Next:** [Health Monitor Cheatsheet](./02-health-cheatsheet.md)
