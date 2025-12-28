#!/bin/bash

# E-Commerce Platform Demo Script
# Interactive demonstration of AI-Shell capabilities

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print section header
print_header() {
    echo ""
    echo -e "${BLUE}=========================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${BLUE}=========================================${NC}"
    echo ""
}

# Function to wait for user
wait_for_user() {
    echo ""
    echo -e "${YELLOW}Press Enter to continue...${NC}"
    read
}

# Function to run AI-Shell command
run_aishell() {
    local query="$1"
    echo -e "${GREEN}AI-Shell Query:${NC} ${query}"
    echo ""
    # This would actually call ai-shell with the query
    # For demo purposes, we'll simulate with SQL/queries
    echo -e "${CYAN}[Simulated response - integrate with actual AI-Shell]${NC}"
}

clear

echo -e "${CYAN}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     E-Commerce Platform - AI-Shell Demo                  ║
║     Multi-Database Management Made Easy                  ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

echo "This demo showcases AI-Shell's capabilities for managing"
echo "a production e-commerce platform with multiple databases."
echo ""
echo "We'll demonstrate:"
echo "  1. Natural language queries across databases"
echo "  2. Performance monitoring and optimization"
echo "  3. Inventory management"
echo "  4. Customer analytics"
echo "  5. Automated operations"
echo ""

wait_for_user

# Demo 1: Product Performance Analysis
print_header "1. Product Performance Analysis"
echo "Let's analyze product performance by combining data from"
echo "PostgreSQL (orders) and MongoDB (reviews)"
echo ""

run_aishell "Show me top 10 products by revenue with their average ratings"

echo "Expected: Federated query joining:"
echo "  - PostgreSQL: products, orders, order_items"
echo "  - MongoDB: reviews collection"
echo "  - Result: Products ranked by revenue with star ratings"
echo ""

# Show actual SQL that would be generated
cat << 'EOF'
Generated Query:
-----------------
-- PostgreSQL query
SELECT
    p.id, p.name, p.sku,
    SUM(oi.subtotal) as total_revenue,
    COUNT(DISTINCT o.id) as order_count,
    SUM(oi.quantity) as units_sold
FROM products p
JOIN order_items oi ON p.id = oi.product_id
JOIN orders o ON oi.order_id = o.id
WHERE o.status IN ('delivered', 'shipped')
GROUP BY p.id
ORDER BY total_revenue DESC
LIMIT 10;

-- MongoDB aggregation
db.reviews.aggregate([
  { $group: {
      _id: "$product_id",
      avg_rating: { $avg: "$rating" },
      review_count: { $sum: 1 }
  }}
])

-- AI-Shell federates the results automatically
EOF

wait_for_user

# Demo 2: Abandoned Cart Recovery
print_header "2. Abandoned Cart Recovery"
echo "Find high-value abandoned carts to trigger recovery campaigns"
echo ""

run_aishell "Which customers have abandoned carts worth more than $500?"

echo ""
echo "This query:"
echo "  1. Identifies abandoned carts (status = 'abandoned')"
echo "  2. Calculates cart value from cart_items"
echo "  3. Filters by value threshold"
echo "  4. Returns customer contact info for recovery"
echo ""

docker-compose exec -T postgres psql -U admin -d ecommerce << 'EOF'
SELECT
    c.id, c.email, c.first_name, c.last_name,
    cart.id as cart_id,
    SUM(p.price * ci.quantity) as cart_value,
    cart.abandoned_at
FROM carts cart
JOIN customers c ON cart.customer_id = c.id
JOIN cart_items ci ON cart.id = ci.cart_id
JOIN products p ON ci.product_id = p.id
WHERE cart.status = 'abandoned'
GROUP BY c.id, cart.id
HAVING SUM(p.price * ci.quantity) > 500
ORDER BY cart_value DESC
LIMIT 10;
EOF

wait_for_user

# Demo 3: Performance Monitoring
print_header "3. Performance Monitoring"
echo "Let's check database performance and get optimization suggestions"
echo ""

run_aishell "Find slow queries in the last hour and suggest optimizations"

echo ""
echo "AI-Shell analyzes:"
echo "  - Query execution times"
echo "  - Missing indexes"
echo "  - Table scan patterns"
echo "  - Connection pool usage"
echo ""

# Show slow queries
docker-compose exec -T postgres psql -U admin -d ecommerce << 'EOF'
-- Check for missing indexes on frequently joined columns
SELECT
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats
WHERE schemaname = 'public'
AND correlation < 0.1
ORDER BY n_distinct DESC
LIMIT 5;
EOF

echo ""
echo -e "${GREEN}Recommendation:${NC} Add index on products(category_id)"
echo -e "${GREEN}Expected improvement:${NC} 10x faster category queries"

wait_for_user

# Demo 4: Inventory Management
print_header "4. Smart Inventory Management"
echo "Identify products that need restocking based on sales trends"
echo ""

run_aishell "Find products with stock below reorder point and check if they're trending"

echo ""
docker-compose exec -T postgres psql -U admin -d ecommerce << 'EOF'
WITH recent_sales AS (
    SELECT
        product_id,
        SUM(quantity) as units_sold_30d
    FROM order_items oi
    JOIN orders o ON oi.order_id = o.id
    WHERE o.created_at > CURRENT_DATE - INTERVAL '30 days'
    AND o.status IN ('delivered', 'shipped')
    GROUP BY product_id
)
SELECT
    p.id, p.sku, p.name,
    p.stock as current_stock,
    p.reorder_point,
    COALESCE(rs.units_sold_30d, 0) as recent_sales,
    p.price * p.stock as stock_value,
    CASE
        WHEN COALESCE(rs.units_sold_30d, 0) > 100 THEN 'High Priority'
        WHEN COALESCE(rs.units_sold_30d, 0) > 50 THEN 'Medium Priority'
        ELSE 'Low Priority'
    END as urgency
FROM products p
LEFT JOIN recent_sales rs ON p.id = rs.product_id
WHERE p.stock < p.reorder_point
AND p.is_active = true
ORDER BY rs.units_sold_30d DESC NULLS LAST
LIMIT 10;
EOF

wait_for_user

# Demo 5: Customer Analytics
print_header "5. VIP Customer Analysis"
echo "Identify VIP customers and their behavior patterns"
echo ""

run_aishell "Show me VIP customers with their lifetime value and recent activity"

echo ""
docker-compose exec -T postgres psql -U admin -d ecommerce << 'EOF'
WITH customer_stats AS (
    SELECT
        customer_id,
        COUNT(*) as total_orders,
        MAX(created_at) as last_order_date,
        AVG(total) as avg_order_value
    FROM orders
    WHERE status IN ('delivered', 'shipped')
    GROUP BY customer_id
)
SELECT
    c.id, c.email, c.first_name, c.last_name,
    c.lifetime_value,
    cs.total_orders,
    cs.avg_order_value::decimal(10,2),
    cs.last_order_date,
    CURRENT_DATE - cs.last_order_date::date as days_since_last_order,
    CASE
        WHEN CURRENT_DATE - cs.last_order_date::date < 30 THEN 'Active'
        WHEN CURRENT_DATE - cs.last_order_date::date < 90 THEN 'At Risk'
        ELSE 'Churned'
    END as customer_status
FROM customers c
JOIN customer_stats cs ON c.id = cs.customer_id
WHERE c.lifetime_value > 10000
ORDER BY c.lifetime_value DESC
LIMIT 10;
EOF

wait_for_user

# Demo 6: Cache Performance
print_header "6. Cache Performance Analysis"
echo "Check Redis cache hit rate and performance"
echo ""

run_aishell "What's the current cache hit rate and should we scale Redis?"

echo ""
echo "Checking Redis statistics..."
docker-compose exec -T redis redis-cli INFO stats | grep -E "keyspace_hits|keyspace_misses|used_memory_human"

echo ""
docker-compose exec -T redis redis-cli << 'EOF'
INFO stats
EOF

echo ""
echo -e "${GREEN}Analysis:${NC}"
echo "  • Cache hit rate: Calculate from hits/(hits+misses)"
echo "  • Memory usage: Current vs max_memory limit"
echo "  • Eviction policy: allkeys-lru"
echo ""
echo -e "${YELLOW}Recommendation:${NC}"
echo "  • Hit rate > 90%: Excellent"
echo "  • Hit rate 70-90%: Good"
echo "  • Hit rate < 70%: Review caching strategy"

wait_for_user

# Demo 7: Review Sentiment Analysis
print_header "7. Product Review Sentiment Analysis"
echo "Analyze product reviews to identify quality issues"
echo ""

run_aishell "Show products with high sales but low ratings - might have quality issues"

echo ""
echo "Querying MongoDB for sentiment analysis..."
docker-compose exec -T mongodb mongosh ecommerce --quiet --eval '
db.reviews.aggregate([
  {
    $group: {
      _id: "$product_id",
      avg_rating: { $avg: "$rating" },
      review_count: { $sum: 1 },
      negative_reviews: {
        $sum: {
          $cond: [{ $lte: ["$rating", 2] }, 1, 0]
        }
      }
    }
  },
  {
    $match: {
      review_count: { $gte: 10 },
      avg_rating: { $lt: 3.5 }
    }
  },
  { $sort: { negative_reviews: -1 } },
  { $limit: 5 }
]).pretty()
'

wait_for_user

# Demo 8: Automated Operations
print_header "8. Automated Database Operations"
echo "AI-Shell can automate routine operations"
echo ""

echo "Example automations:"
echo ""
echo "1. Backup Scheduling"
run_aishell "Schedule daily backups at 2 AM and keep 7 days of history"
echo "   → Configures cron job for pg_dump and mongodump"
echo ""

echo "2. Performance Monitoring"
run_aishell "Alert me when slow query count exceeds 10 per hour"
echo "   → Sets up monitoring with Slack/email notifications"
echo ""

echo "3. Index Optimization"
run_aishell "Automatically create indexes for columns used in WHERE clauses"
echo "   → Analyzes query patterns and suggests indexes"
echo ""

echo "4. Cache Warming"
run_aishell "Pre-load top 1000 products into Redis cache"
echo "   → Queries products and populates cache"
echo ""

wait_for_user

# Final Summary
print_header "Demo Complete!"

echo "You've seen AI-Shell manage:"
echo ""
echo -e "  ${GREEN}✓${NC} Multi-database queries (PostgreSQL + MongoDB + Redis)"
echo -e "  ${GREEN}✓${NC} Performance monitoring and optimization"
echo -e "  ${GREEN}✓${NC} Inventory management and alerts"
echo -e "  ${GREEN}✓${NC} Customer analytics and segmentation"
echo -e "  ${GREEN}✓${NC} Cache performance analysis"
echo -e "  ${GREEN}✓${NC} Review sentiment analysis"
echo -e "  ${GREEN}✓${NC} Automated operations and scheduling"
echo ""
echo "All using natural language queries!"
echo ""
echo -e "${CYAN}Next Steps:${NC}"
echo "  1. Try your own queries:  ai-shell"
echo "  2. View documentation:    cat README.md"
echo "  3. Check the config:      cat config/ai-shell.config.json"
echo "  4. Explore data:          http://localhost:8080"
echo ""
echo -e "${YELLOW}Commands:${NC}"
echo "  • View logs:       docker-compose logs -f"
echo "  • Stop services:   docker-compose down"
echo "  • Restart:         docker-compose restart"
echo "  • Cleanup:         ./scripts/cleanup.sh"
echo ""
echo -e "${GREEN}Happy querying!${NC}"
echo ""
