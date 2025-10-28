#!/bin/bash

#
# Basic Query Optimization Examples
# Demonstrates the query optimization commands
#

set -e

echo "🚀 AI-Shell Query Optimization Examples"
echo "========================================"
echo ""

# Check for API key
if [ -z "$ANTHROPIC_API_KEY" ]; then
  echo "❌ Error: ANTHROPIC_API_KEY not set"
  echo "Please set your Anthropic API key:"
  echo "  export ANTHROPIC_API_KEY=your-api-key"
  exit 1
fi

# Example 1: Basic optimization
echo "1️⃣  Basic Query Optimization"
echo "----------------------------"
ai-shell optimize "SELECT * FROM users WHERE id > 100" --format text
echo ""

# Example 2: Optimization with execution plan
echo "2️⃣  Optimization with Execution Plan"
echo "------------------------------------"
ai-shell optimize "SELECT u.*, o.* FROM users u JOIN orders o ON u.id = o.user_id" --explain
echo ""

# Example 3: Slow query analysis
echo "3️⃣  Slow Query Analysis"
echo "-----------------------"
ai-shell slow-queries --threshold 500 --limit 5
echo ""

# Example 4: Index recommendations
echo "4️⃣  Index Recommendations"
echo "-------------------------"
ai-shell indexes recommend --table users
echo ""

# Example 5: Risk check
echo "5️⃣  Risk Check"
echo "--------------"
ai-shell risk-check "DELETE FROM orders WHERE status = 'cancelled'"
echo ""

# Example 6: Safe dry-run
echo "6️⃣  Safe Dry-Run"
echo "----------------"
ai-shell optimize "UPDATE users SET active = true" --dry-run
echo ""

echo "✅ Examples completed successfully!"
echo ""
echo "💡 Tips:"
echo "  • Always use --dry-run for destructive operations"
echo "  • Run risk-check before executing dangerous queries"
echo "  • Use --format json for programmatic processing"
echo "  • Enable --verbose for detailed logging"
