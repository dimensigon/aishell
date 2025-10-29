# Redis Complete Guide

A comprehensive tutorial for Redis in-memory data store, from basics to advanced patterns.

**Estimated Time:** 5-6 hours
**Prerequisites:** Basic database knowledge, Docker installed

---

## Table of Contents

1. [Setup and Installation](#1-setup-and-installation)
2. [Redis Data Types](#2-redis-data-types)
3. [String Operations](#3-string-operations)
4. [Hash Operations](#4-hash-operations)
5. [List Operations](#5-list-operations)
6. [Set Operations](#6-set-operations)
7. [Sorted Set Operations](#7-sorted-set-operations)
8. [Caching Patterns](#8-caching-patterns)
9. [Pub/Sub Messaging](#9-pubsub-messaging)
10. [Transactions and Pipelining](#10-transactions-and-pipelining)
11. [Persistence and Durability](#11-persistence-and-durability)
12. [Performance and Optimization](#12-performance-and-optimization)
13. [Real-World Use Cases](#13-real-world-use-cases)
14. [Troubleshooting](#14-troubleshooting)

---

## 1. Setup and Installation

**Time:** 20 minutes

### 1.1 Docker Setup

```bash
# Pull Redis image
docker pull redis:7

# Run Redis container
docker run -d \
  --name my-redis \
  -p 6379:6379 \
  -v redis-data:/data \
  redis:7 redis-server --appendonly yes

# Verify container is running
docker ps | grep redis
```

### 1.2 Connect to Redis

```bash
# Using docker exec
docker exec -it my-redis redis-cli

# Using AIShell
aishell redis connect --host localhost --port 6379

# Test connection
PING
# Output: PONG
```

### 1.3 Basic Configuration

```bash
# Inside redis-cli

# Check Redis version
INFO server

# Get all configuration
CONFIG GET *

# Set maxmemory
CONFIG SET maxmemory 256mb
CONFIG SET maxmemory-policy allkeys-lru

# Save configuration
CONFIG REWRITE

# Check database size
DBSIZE

# Select database (0-15 by default)
SELECT 1

# Clear current database
FLUSHDB

# Clear all databases
FLUSHALL
```

**Expected Output:**
```
Redis server v=7.x.x
```

**Exercise 1.1:** Configure Redis for production
- Set memory limit to 512MB
- Enable AOF persistence
- Set eviction policy to allkeys-lru
- Verify settings

<details>
<summary>Solution</summary>

```bash
# Connect to Redis
docker exec -it my-redis redis-cli

# Configure memory
CONFIG SET maxmemory 512mb
CONFIG GET maxmemory

# Set eviction policy
CONFIG SET maxmemory-policy allkeys-lru
CONFIG GET maxmemory-policy

# Enable AOF (already enabled in docker run)
CONFIG GET appendonly

# Save configuration
CONFIG REWRITE

# Verify all settings
CONFIG GET maxmemory*
CONFIG GET appendonly
CONFIG GET save

# Check info
INFO memory
INFO persistence
```
</details>

---

## 2. Redis Data Types

**Time:** 30 minutes

Redis supports 5 main data types and several specialized types:

### 2.1 Data Type Overview

```bash
# STRING - Binary-safe strings up to 512MB
SET key "value"

# HASH - Maps between string fields and values
HSET user:1 name "John" email "john@example.com"

# LIST - Ordered collections of strings
LPUSH mylist "item1" "item2"

# SET - Unordered collections of unique strings
SADD myset "member1" "member2"

# SORTED SET - Sets ordered by score
ZADD leaderboard 100 "player1" 200 "player2"

# Check type of key
TYPE key
```

### 2.2 Key Naming Conventions

```bash
# Best practices for key names

# Use namespaces with colons
SET user:1000:name "John Doe"
SET user:1000:email "john@example.com"

# Use descriptive names
SET session:abc123:token "xyz789"
SET cache:product:1234 "{\"name\":\"Laptop\"}"

# Avoid very long keys (memory and performance)
# BAD: SET this_is_a_very_long_key_name_that_wastes_memory "value"
# GOOD: SET user:1000:session "value"

# Use consistent naming patterns
SET order:5678:status "shipped"
SET order:5678:total "99.99"
SET order:5678:customer_id "1000"
```

### 2.3 Key Management

```bash
# Check if key exists
EXISTS user:1000

# Delete key
DEL user:1000

# Delete multiple keys
DEL user:1001 user:1002 user:1003

# Set expiration (TTL in seconds)
EXPIRE user:1000 3600

# Set expiration at specific time
EXPIREAT user:1000 1704067200

# Check TTL
TTL user:1000

# Remove expiration
PERSIST user:1000

# Rename key
RENAME oldkey newkey

# Get all keys matching pattern
KEYS user:*

# Scan keys (better for production)
SCAN 0 MATCH user:* COUNT 100

# Get random key
RANDOMKEY
```

**Exercise 2.1:** Key management practice
- Create 10 user keys with different fields
- Set expiration on some keys
- Find all keys matching pattern
- Delete expired keys

<details>
<summary>Solution</summary>

```bash
# Create users
for i in {1..10}; do
  redis-cli HSET user:$i name "User$i" email "user$i@example.com" age $((20 + i))
done

# Set expiration on odd-numbered users (1 hour)
for i in {1..10..2}; do
  redis-cli EXPIRE user:$i 3600
done

# Find all user keys
redis-cli KEYS "user:*"

# Better: use SCAN
redis-cli SCAN 0 MATCH "user:*" COUNT 100

# Check TTL for each key
for i in {1..10}; do
  echo "user:$i TTL: $(redis-cli TTL user:$i)"
done

# Get all users with their TTL
redis-cli --eval - <<'EOF'
local keys = redis.call('KEYS', 'user:*')
local result = {}
for i, key in ipairs(keys) do
  local ttl = redis.call('TTL', key)
  table.insert(result, key .. ' TTL: ' .. ttl)
end
return result
EOF

# Delete keys with TTL < 0 (already expired)
for key in $(redis-cli KEYS "user:*"); do
  ttl=$(redis-cli TTL $key)
  if [ $ttl -eq -2 ]; then
    redis-cli DEL $key
    echo "Deleted expired key: $key"
  fi
done
```
</details>

---

## 3. String Operations

**Time:** 30 minutes

### 3.1 Basic String Commands

```bash
# Set and get
SET name "John Doe"
GET name

# Set with expiration
SETEX session:abc123 3600 "user_data"

# Set only if not exists
SETNX lock:resource1 "locked"

# Set multiple keys
MSET user:1:name "John" user:1:email "john@example.com" user:1:age "30"

# Get multiple keys
MGET user:1:name user:1:email user:1:age

# Append to string
APPEND name " Jr."
GET name

# Get string length
STRLEN name

# Get substring
GETRANGE name 0 3

# Set range
SETRANGE name 0 "Jane"
```

### 3.2 Numeric Operations

```bash
# Increment
SET counter 0
INCR counter
INCRBY counter 5
INCRBYFLOAT price 10.50

# Decrement
DECR counter
DECRBY counter 3

# Atomic increment and get
SET views 100
INCR views
GET views
```

### 3.3 Bit Operations

```bash
# Set bit
SETBIT user:1000:permissions 0 1
SETBIT user:1000:permissions 2 1
SETBIT user:1000:permissions 5 1

# Get bit
GETBIT user:1000:permissions 0

# Count bits
BITCOUNT user:1000:permissions

# Bitwise operations
SETBIT key1 0 1
SETBIT key2 0 1
BITOP AND result key1 key2
```

**Exercise 3.1:** Build a view counter and visitor tracker
- Track page views with atomic increments
- Track unique visitors using bit operations
- Implement rate limiting

<details>
<summary>Solution</summary>

```bash
# Page view counter
SET page:home:views 0
SET page:about:views 0

# Increment views
INCR page:home:views
INCRBY page:home:views 5

# Get all page views
MGET page:home:views page:about:views

# Track unique visitors by date using bitmaps
# User ID as offset in bitmap
SETBIT visitors:2024-01-15 1000 1
SETBIT visitors:2024-01-15 1001 1
SETBIT visitors:2024-01-15 1002 1

# Check if user visited
GETBIT visitors:2024-01-15 1000

# Count unique visitors
BITCOUNT visitors:2024-01-15

# Rate limiting: max 10 requests per minute
# Returns 1 if allowed, 0 if rate limited
redis-cli --eval - user:1000 60 10 <<'EOF'
local key = "ratelimit:" .. KEYS[1] .. ":" .. math.floor(redis.call('TIME')[1] / ARGV[1])
local current = redis.call('INCR', key)
if current == 1 then
  redis.call('EXPIRE', key, ARGV[1])
end
if current > tonumber(ARGV[2]) then
  return 0
else
  return 1
end
EOF

# Test rate limiting
for i in {1..15}; do
  result=$(redis-cli --eval rate-limit.lua user:1000 60 10)
  echo "Request $i: $result"
  sleep 0.1
done
```

Rate limiting Lua script (rate-limit.lua):
```lua
local key = "ratelimit:" .. KEYS[1] .. ":" .. math.floor(redis.call('TIME')[1] / ARGV[1])
local current = redis.call('INCR', key)
if current == 1 then
  redis.call('EXPIRE', key, ARGV[1])
end
if current > tonumber(ARGV[2]) then
  return 0
else
  return 1
end
```
</details>

---

## 4. Hash Operations

**Time:** 30 minutes

### 4.1 Basic Hash Commands

```bash
# Set single field
HSET user:1000 name "John Doe"

# Set multiple fields
HSET user:1000 email "john@example.com" age 30 city "New York"

# Get single field
HGET user:1000 name

# Get multiple fields
HMGET user:1000 name email age

# Get all fields and values
HGETALL user:1000

# Get all field names
HKEYS user:1000

# Get all values
HVALS user:1000

# Check if field exists
HEXISTS user:1000 email

# Delete field
HDEL user:1000 city

# Get number of fields
HLEN user:1000

# Set if not exists
HSETNX user:1000 created_at "2024-01-15"
```

### 4.2 Numeric Operations on Hashes

```bash
# Increment field
HSET product:1234 price 99.99
HINCRBYFLOAT product:1234 price 10.00
HGET product:1234 price

# Decrement using negative increment
HSET product:1234 stock 100
HINCRBY product:1234 stock -5
HGET product:1234 stock
```

### 4.3 Scanning Hash Fields

```bash
# Scan hash fields
HSCAN user:1000 0 MATCH "email*" COUNT 10
```

**Exercise 4.1:** Build a user profile system
- Store user profiles with multiple fields
- Update specific fields atomically
- Implement counters for user statistics

<details>
<summary>Solution</summary>

```bash
# Create user profile
HSET user:1000 \
  username "johndoe" \
  email "john@example.com" \
  first_name "John" \
  last_name "Doe" \
  age 30 \
  city "New York" \
  country "USA" \
  created_at "2024-01-15T10:00:00Z"

# Add user statistics
HSET user:1000:stats \
  posts 0 \
  followers 0 \
  following 0 \
  likes_received 0

# Update user field
HSET user:1000 city "Los Angeles"

# Increment stats atomically
HINCRBY user:1000:stats posts 1
HINCRBY user:1000:stats followers 5
HINCRBY user:1000:stats likes_received 10

# Get full profile
HGETALL user:1000

# Get specific fields
HMGET user:1000 username email city

# Get all stats
HGETALL user:1000:stats

# Check if email exists
HEXISTS user:1000 email

# Get user count
HLEN user:1000

# Update profile with validation
redis-cli --eval - user:1000 age 31 <<'EOF'
local user_key = KEYS[1]
local field = ARGV[1]
local value = tonumber(ARGV[2])

if value < 18 or value > 120 then
  return redis.error_reply("Invalid age")
end

redis.call('HSET', user_key, field, value)
return redis.status_reply("OK")
EOF

# Batch update multiple users
redis-cli --pipe <<'EOF'
HSET user:1001 username "alice" email "alice@example.com"
HSET user:1002 username "bob" email "bob@example.com"
HSET user:1003 username "carol" email "carol@example.com"
EOF

# Get all user IDs
redis-cli KEYS "user:[0-9]*" | grep -v stats
```
</details>

---

## 5. List Operations

**Time:** 45 minutes

### 5.1 Basic List Commands

```bash
# Push to left (head)
LPUSH mylist "item1" "item2" "item3"

# Push to right (tail)
RPUSH mylist "item4" "item5"

# Get list length
LLEN mylist

# Get elements by range
LRANGE mylist 0 -1  # All elements
LRANGE mylist 0 2   # First 3 elements

# Get element by index
LINDEX mylist 0

# Set element by index
LSET mylist 0 "new_value"

# Pop from left
LPOP mylist

# Pop from right
RPOP mylist

# Pop from left with timeout (blocking)
BLPOP mylist 5

# Trim list
LTRIM mylist 0 99  # Keep first 100 elements
```

### 5.2 List as Queue (FIFO)

```bash
# Enqueue (add to tail)
RPUSH queue:tasks "task1" "task2" "task3"

# Dequeue (remove from head)
LPOP queue:tasks

# Blocking dequeue (wait for item)
BLPOP queue:tasks 0  # Wait forever
```

### 5.3 List as Stack (LIFO)

```bash
# Push
LPUSH stack:undo "action1" "action2"

# Pop
LPOP stack:undo
```

### 5.4 Advanced List Operations

```bash
# Insert before/after
LINSERT mylist BEFORE "item2" "new_item"
LINSERT mylist AFTER "item2" "another_item"

# Remove elements
LREM mylist 2 "item1"  # Remove first 2 occurrences
LREM mylist -1 "item1" # Remove last occurrence
LREM mylist 0 "item1"  # Remove all occurrences

# Atomic move between lists
RPOPLPUSH source destination

# Blocking move
BRPOPLPUSH source destination 5
```

**Exercise 5.1:** Implement a job queue and activity feed
- Create task queue with priority
- Implement recent activity feed
- Build undo/redo functionality

<details>
<summary>Solution</summary>

```bash
# Job Queue Implementation

# Add jobs to queue
RPUSH queue:jobs '{"id":1,"type":"email","priority":"high"}'
RPUSH queue:jobs '{"id":2,"type":"pdf","priority":"normal"}'
RPUSH queue:jobs '{"id":3,"type":"email","priority":"high"}'

# Process job (blocking, waits for job)
BLPOP queue:jobs 0

# Add job with priority (separate queues)
RPUSH queue:high '{"id":1,"type":"email"}'
RPUSH queue:normal '{"id":2,"type":"pdf"}'
RPUSH queue:low '{"id":3,"type":"cleanup"}'

# Process jobs by priority
redis-cli --eval - queue:high queue:normal queue:low 5 <<'EOF'
local high = KEYS[1]
local normal = KEYS[2]
local low = KEYS[3]
local timeout = tonumber(ARGV[1])

-- Try high priority first
local job = redis.call('LPOP', high)
if job then return job end

-- Then normal priority
job = redis.call('LPOP', normal)
if job then return job end

-- Finally low priority
job = redis.call('LPOP', low)
if job then return job end

-- Use blocking pop if all empty
return redis.call('BLPOP', high, normal, low, timeout)
EOF

# Activity Feed (keep last 100 activities)
add_activity() {
  local user_id=$1
  local activity=$2
  redis-cli LPUSH "feed:$user_id" "$activity"
  redis-cli LTRIM "feed:$user_id" 0 99
}

# Add activities
add_activity 1000 '{"action":"posted","content":"Hello World","time":"2024-01-15T10:00:00Z"}'
add_activity 1000 '{"action":"liked","post_id":123,"time":"2024-01-15T10:05:00Z"}'
add_activity 1000 '{"action":"commented","post_id":456,"time":"2024-01-15T10:10:00Z"}'

# Get recent activities
LRANGE feed:1000 0 9  # Last 10 activities

# Undo/Redo Implementation

# Initialize stacks
LPUSH undo:1000 '{"action":"delete","id":1}'
LPUSH undo:1000 '{"action":"edit","id":2,"old":"old text"}'

# Undo operation
undo() {
  local user_id=$1
  local action=$(redis-cli LPOP "undo:$user_id")
  if [ -n "$action" ]; then
    redis-cli LPUSH "redo:$user_id" "$action"
    echo "Undone: $action"
  else
    echo "Nothing to undo"
  fi
}

# Redo operation
redo() {
  local user_id=$1
  local action=$(redis-cli LPOP "redo:$user_id")
  if [ -n "$action" ]; then
    redis-cli LPUSH "undo:$user_id" "$action"
    echo "Redone: $action"
  else
    echo "Nothing to redo"
  fi
}

# Test undo/redo
undo 1000
undo 1000
redo 1000

# Delayed Job Queue (using sorted set for timing)
ZADD delayed:jobs $(date -d "+5 minutes" +%s) '{"id":1,"type":"email"}'
ZADD delayed:jobs $(date -d "+10 minutes" +%s) '{"id":2,"type":"pdf"}'

# Process delayed jobs
redis-cli --eval - delayed:jobs <<'EOF'
local now = redis.call('TIME')[1]
local jobs = redis.call('ZRANGEBYSCORE', KEYS[1], '-inf', now)
if #jobs > 0 then
  redis.call('ZREMRANGEBYSCORE', KEYS[1], '-inf', now)
  return jobs
end
return {}
EOF
```
</details>

---

## 6. Set Operations

**Time:** 30 minutes

### 6.1 Basic Set Commands

```bash
# Add members
SADD myset "member1" "member2" "member3"

# Check if member exists
SISMEMBER myset "member1"

# Get all members
SMEMBERS myset

# Get number of members
SCARD myset

# Remove member
SREM myset "member1"

# Pop random member
SPOP myset

# Get random member (without removing)
SRANDMEMBER myset
SRANDMEMBER myset 3  # Get 3 random members
```

### 6.2 Set Operations

```bash
# Create sets
SADD set1 "a" "b" "c" "d"
SADD set2 "c" "d" "e" "f"

# Union
SUNION set1 set2

# Intersection
SINTER set1 set2

# Difference
SDIFF set1 set2

# Store result
SUNIONSTORE result set1 set2
SINTERSTORE result set1 set2
SDIFFSTORE result set1 set2

# Move member between sets
SMOVE set1 set2 "a"
```

### 6.3 Scanning Sets

```bash
# Scan members
SSCAN myset 0 MATCH "member*" COUNT 10
```

**Exercise 6.1:** Build a tagging and recommendation system
- Tag items with categories
- Find items with multiple tags
- Build "users who liked this also liked" feature

<details>
<summary>Solution</summary>

```bash
# Tagging System

# Tag products
SADD product:1234:tags "electronics" "laptop" "gaming" "portable"
SADD product:5678:tags "electronics" "phone" "5g" "portable"
SADD product:9012:tags "electronics" "tablet" "portable" "education"

# Find all products with "electronics" tag
SMEMBERS tag:electronics:products

# Better approach: maintain reverse index
SADD tag:electronics 1234 5678 9012
SADD tag:laptop 1234
SADD tag:phone 5678
SADD tag:portable 1234 5678 9012

# Find products with both "electronics" AND "portable"
SINTER tag:electronics tag:portable

# Find products with "electronics" OR "phone"
SUNION tag:electronics tag:phone

# Find products with "electronics" but NOT "phone"
SDIFF tag:electronics tag:phone

# User interests
SADD user:1000:interests "gaming" "technology" "music"
SADD user:1001:interests "gaming" "sports" "technology"

# Find common interests
SINTER user:1000:interests user:1001:interests

# Recommendation System

# Track user likes
SADD user:1000:likes product:1234 product:5678
SADD user:1001:likes product:1234 product:9012
SADD user:1002:likes product:1234 product:5678 product:9012

# Track product likes (reverse index)
SADD product:1234:likers user:1000 user:1001 user:1002
SADD product:5678:likers user:1000 user:1002
SADD product:9012:likers user:1001 user:1002

# Find users who liked the same product
SINTER product:1234:likers product:5678:likers

# Recommend products: "Users who liked X also liked Y"
redis-cli --eval - user:1000 product:1234 5 <<'EOF'
local user_id = ARGV[1]
local product_id = ARGV[2]
local limit = tonumber(ARGV[3])

-- Get users who liked this product
local similar_users = redis.call('SMEMBERS', 'product:' .. product_id .. ':likers')

-- Get all products liked by similar users
local recommended = {}
for _, similar_user in ipairs(similar_users) do
  if similar_user ~= user_id then
    local products = redis.call('SMEMBERS', 'user:' .. similar_user .. ':likes')
    for _, product in ipairs(products) do
      if product ~= product_id then
        recommended[product] = (recommended[product] or 0) + 1
      end
    end
  end
end

-- Sort by frequency
local sorted = {}
for product, count in pairs(recommended) do
  table.insert(sorted, {product, count})
end
table.sort(sorted, function(a, b) return a[2] > b[2] end)

-- Return top N
local result = {}
for i = 1, math.min(limit, #sorted) do
  table.insert(result, sorted[i][1])
end
return result
EOF

# Find similar users
SINTER user:1000:likes user:1001:likes

# Social network: followers/following
SADD user:1000:following user:1001 user:1002
SADD user:1001:followers user:1000
SADD user:1002:followers user:1000

# Mutual followers
SINTER user:1000:following user:1001:following

# Suggested follows (friends of friends)
SUNION user:1001:following user:1002:following
SDIFF <above> user:1000:following  # Remove already following
```
</details>

---

## 7. Sorted Set Operations

**Time:** 45 minutes

### 7.1 Basic Sorted Set Commands

```bash
# Add members with scores
ZADD leaderboard 100 "player1"
ZADD leaderboard 200 "player2" 150 "player3"

# Get score of member
ZSCORE leaderboard "player1"

# Get rank (0-based, ascending)
ZRANK leaderboard "player1"

# Get rank (descending)
ZREVRANK leaderboard "player1"

# Increment score
ZINCRBY leaderboard 50 "player1"

# Get number of members
ZCARD leaderboard

# Count members in score range
ZCOUNT leaderboard 100 200

# Get members by rank
ZRANGE leaderboard 0 -1           # All, ascending
ZRANGE leaderboard 0 -1 WITHSCORES # With scores
ZREVRANGE leaderboard 0 9 WITHSCORES # Top 10, descending

# Get members by score
ZRANGEBYSCORE leaderboard 100 200
ZRANGEBYSCORE leaderboard -inf +inf WITHSCORES LIMIT 0 10

# Remove members
ZREM leaderboard "player1"

# Remove by rank
ZREMRANGEBYRANK leaderboard 0 2  # Remove first 3

# Remove by score
ZREMRANGEBYSCORE leaderboard 0 100
```

### 7.2 Sorted Set Operations

```bash
# Create sorted sets
ZADD set1 1 "a" 2 "b" 3 "c"
ZADD set2 1 "b" 2 "c" 3 "d"

# Union with sum of scores
ZUNIONSTORE result 2 set1 set2

# Union with max/min scores
ZUNIONSTORE result 2 set1 set2 AGGREGATE MAX

# Intersection
ZINTERSTORE result 2 set1 set2

# With weights
ZUNIONSTORE result 2 set1 set2 WEIGHTS 2 3
```

### 7.3 Lexicographic Operations

```bash
# Add members with same score for lexicographic sorting
ZADD words 0 "apple" 0 "banana" 0 "cherry" 0 "date"

# Range by lex
ZRANGEBYLEX words [a [c  # From 'a' to 'c'
ZRANGEBYLEX words - [c   # From start to 'c'

# Remove by lex
ZREMRANGEBYLEX words [a [b
```

**Exercise 7.1:** Build a leaderboard and priority queue
- Gaming leaderboard with scores
- Trending posts by engagement score
- Time-based event scheduling

<details>
<summary>Solution</summary>

```bash
# Gaming Leaderboard

# Add players with scores
ZADD game:leaderboard 1500 "player1"
ZADD game:leaderboard 2000 "player2"
ZADD game:leaderboard 1800 "player3"
ZADD game:leaderboard 2200 "player4"
ZADD game:leaderboard 1950 "player5"

# Update score after game
ZINCRBY game:leaderboard 100 "player1"
ZINCRBY game:leaderboard -50 "player2"

# Get top 10 players
ZREVRANGE game:leaderboard 0 9 WITHSCORES

# Get player rank
ZREVRANK game:leaderboard "player1"

# Get players in score range
ZRANGEBYSCORE game:leaderboard 1800 2000 WITHSCORES

# Get player's score
ZSCORE game:leaderboard "player1"

# Get surrounding players (context)
redis-cli --eval - game:leaderboard player1 2 <<'EOF'
local key = KEYS[1]
local player = ARGV[1]
local range = tonumber(ARGV[2])

local rank = redis.call('ZREVRANK', key, player)
if not rank then return nil end

local start = math.max(0, rank - range)
local stop = rank + range

return redis.call('ZREVRANGE', key, start, stop, 'WITHSCORES')
EOF

# Trending Posts (time-decay scoring)

# Add post with engagement score
add_post() {
  local post_id=$1
  local likes=$2
  local comments=$3
  local shares=$4
  local timestamp=$(date +%s)

  # Calculate engagement score with time decay
  # Score = (likes * 1 + comments * 2 + shares * 3) / age_hours
  local age_hours=$(( (timestamp - $(date -d "2024-01-01" +%s)) / 3600 ))
  local score=$(echo "scale=2; ($likes + $comments * 2 + $shares * 3) / ($age_hours + 1)" | bc)

  redis-cli ZADD trending:posts $score $post_id
}

# Add trending posts
add_post "post:1" 100 50 20
add_post "post:2" 200 100 50
add_post "post:3" 50 25 10

# Update post engagement
update_engagement() {
  local post_id=$1
  local new_likes=$2
  local new_comments=$3
  local new_shares=$4

  # Recalculate score
  local timestamp=$(date +%s)
  local age_hours=$(( (timestamp - $(date -d "2024-01-01" +%s)) / 3600 ))
  local score=$(echo "scale=2; ($new_likes + $new_comments * 2 + $new_shares * 3) / ($age_hours + 1)" | bc)

  redis-cli ZADD trending:posts $score $post_id
}

# Get trending posts
ZREVRANGE trending:posts 0 9 WITHSCORES

# Remove old posts (score < threshold)
ZREMRANGEBYSCORE trending:posts -inf 1.0

# Time-based Event Scheduling

# Schedule events (score = unix timestamp)
ZADD scheduled:events $(date -d "+1 hour" +%s) "event:1"
ZADD scheduled:events $(date -d "+2 hours" +%s) "event:2"
ZADD scheduled:events $(date -d "+30 minutes" +%s) "event:3"

# Get events due now
current_time=$(date +%s)
ZRANGEBYSCORE scheduled:events -inf $current_time

# Process due events
redis-cli --eval - scheduled:events <<'EOF'
local key = KEYS[1]
local now = redis.call('TIME')[1]

-- Get due events
local events = redis.call('ZRANGEBYSCORE', key, '-inf', now)

if #events > 0 then
  -- Remove processed events
  redis.call('ZREMRANGEBYSCORE', key, '-inf', now)
  return events
end

return {}
EOF

# Recurring event: re-add after processing
process_event() {
  local event=$1
  local interval_seconds=$2

  # Process event
  echo "Processing $event"

  # Re-schedule
  local next_time=$(( $(date +%s) + interval_seconds ))
  redis-cli ZADD scheduled:events $next_time $event
}

# Priority Task Queue (higher score = higher priority)

# Add tasks with priority
ZADD task:queue 10 "task:low"
ZADD task:queue 50 "task:medium"
ZADD task:queue 90 "task:high"
ZADD task:queue 100 "task:critical"

# Get highest priority task
ZPOPMAX task:queue

# Get multiple high-priority tasks
ZPOPMAX task:queue 5

# Add task with deadline (score = priority + deadline factor)
add_task_with_deadline() {
  local task=$1
  local priority=$2
  local deadline_hours=$3

  # Higher priority for sooner deadlines
  local deadline_factor=$(echo "scale=2; 1000 / $deadline_hours" | bc)
  local score=$(echo "$priority + $deadline_factor" | bc)

  redis-cli ZADD task:queue $score $task
}

add_task_with_deadline "task:urgent" 50 2
add_task_with_deadline "task:normal" 50 24

# Range Queries (find items in range)

# Product prices
ZADD products:by_price 29.99 "product:1"
ZADD products:by_price 49.99 "product:2"
ZADD products:by_price 99.99 "product:3"

# Find products in price range $25-$75
ZRANGEBYSCORE products:by_price 25 75 WITHSCORES

# Hotel ratings
ZADD hotels:by_rating 4.5 "hotel:1"
ZADD hotels:by_rating 4.8 "hotel:2"
ZADD hotels:by_rating 4.2 "hotel:3"

# Find hotels with rating >= 4.5
ZRANGEBYSCORE hotels:by_rating 4.5 +inf WITHSCORES
```
</details>

---

## 8. Caching Patterns

**Time:** 45 minutes

### 8.1 Cache-Aside Pattern

```bash
# Pseudocode pattern:
# 1. Check cache
# 2. If miss, fetch from database
# 3. Store in cache with TTL
# 4. Return data

# Example: User profile caching
get_user() {
  local user_id=$1

  # Try cache first
  local cached=$(redis-cli GET "cache:user:$user_id")

  if [ -n "$cached" ]; then
    echo "Cache HIT: $cached"
    return
  fi

  # Cache miss - fetch from DB
  echo "Cache MISS - fetching from DB"
  local user_data=$(psql -t -c "SELECT row_to_json(u) FROM users u WHERE id=$user_id")

  # Store in cache for 1 hour
  redis-cli SETEX "cache:user:$user_id" 3600 "$user_data"

  echo "$user_data"
}
```

### 8.2 Write-Through Cache

```bash
# Update cache immediately when data is written

update_user() {
  local user_id=$1
  local new_data=$2

  # Update database
  psql -c "UPDATE users SET data='$new_data' WHERE id=$user_id"

  # Update cache
  redis-cli SET "cache:user:$user_id" "$new_data" EX 3600
}
```

### 8.3 Write-Behind (Write-Back) Cache

```bash
# Write to cache immediately, sync to DB later

update_user_async() {
  local user_id=$1
  local new_data=$2

  # Update cache immediately
  redis-cli SET "cache:user:$user_id" "$new_data" EX 3600

  # Queue for DB update
  redis-cli RPUSH "queue:db_updates" "{\"table\":\"users\",\"id\":$user_id,\"data\":\"$new_data\"}"
}
```

### 8.4 Cache Invalidation Strategies

```bash
# TTL-based invalidation
SETEX cache:key 3600 "value"

# Manual invalidation
DEL cache:user:1000

# Tag-based invalidation
SADD cache:tags:user:1000 cache:user:1000:profile cache:user:1000:settings

# Invalidate all related caches
invalidate_user_caches() {
  local user_id=$1
  local caches=$(redis-cli SMEMBERS "cache:tags:user:$user_id")

  for cache_key in $caches; do
    redis-cli DEL $cache_key
  done

  redis-cli DEL "cache:tags:user:$user_id"
}
```

### 8.5 Cache Warming

```bash
# Preload frequently accessed data

warm_cache() {
  # Fetch top 100 users from DB
  local users=$(psql -t -c "SELECT id, row_to_json(u) FROM users u ORDER BY last_login DESC LIMIT 100")

  while IFS='|' read -r id data; do
    redis-cli SET "cache:user:$id" "$data" EX 3600
  done <<< "$users"

  echo "Cache warmed with 100 users"
}
```

**Exercise 8.1:** Implement a complete caching system
- Cache-aside for read-heavy data
- Write-through for consistency
- Smart cache invalidation
- Cache hit/miss tracking

<details>
<summary>Solution</summary>

```bash
#!/bin/bash
# complete-caching-system.sh

# Cache statistics
increment_cache_stat() {
  local stat=$1
  redis-cli HINCRBY cache:stats $stat 1
}

# Get cache statistics
get_cache_stats() {
  redis-cli HGETALL cache:stats
}

# Cache-aside with statistics
cache_get() {
  local key=$1
  local ttl=${2:-3600}

  # Try cache
  local value=$(redis-cli GET "cache:$key")

  if [ -n "$value" ]; then
    increment_cache_stat "hits"
    echo "$value"
    return 0
  fi

  increment_cache_stat "misses"
  return 1
}

# Set cache with TTL
cache_set() {
  local key=$1
  local value=$2
  local ttl=${3:-3600}

  redis-cli SETEX "cache:$key" $ttl "$value"
  increment_cache_stat "sets"
}

# Invalidate cache
cache_invalidate() {
  local key=$1

  redis-cli DEL "cache:$key"
  increment_cache_stat "invalidations"
}

# Multi-level caching (L1: Redis, L2: Database)
get_with_multilevel_cache() {
  local key=$1

  # L1: Redis cache
  local cached=$(cache_get "$key")
  if [ $? -eq 0 ]; then
    echo "L1 HIT: $cached"
    return
  fi

  # L2: Database
  echo "L1 MISS - checking database"
  local db_value=$(fetch_from_database "$key")

  if [ -n "$db_value" ]; then
    # Populate cache
    cache_set "$key" "$db_value"
    echo "L2 HIT (cached): $db_value"
  else
    # Cache negative result (prevent DB hammering)
    cache_set "$key" "NULL" 60  # Short TTL for negative cache
    echo "L2 MISS"
  fi
}

# Fetch from database (mock)
fetch_from_database() {
  local key=$1
  # Simulate DB query
  sleep 0.1
  echo "{\"key\":\"$key\",\"data\":\"value_from_db\"}"
}

# Tagged cache for group invalidation
cache_set_with_tags() {
  local key=$1
  local value=$2
  local tags=$3  # Space-separated tags

  # Set cache
  cache_set "$key" "$value"

  # Add to tag sets
  for tag in $tags; do
    redis-cli SADD "cache:tag:$tag" "cache:$key"
  done
}

# Invalidate by tag
cache_invalidate_by_tag() {
  local tag=$1

  # Get all keys with this tag
  local keys=$(redis-cli SMEMBERS "cache:tag:$tag")

  # Delete all keys
  for key in $keys; do
    redis-cli DEL "$key"
  done

  # Remove tag set
  redis-cli DEL "cache:tag:$tag"

  increment_cache_stat "tag_invalidations"
}

# Example usage

# Set cache with tags
cache_set_with_tags "user:1000" '{"name":"John"}' "user users"
cache_set_with_tags "user:1001" '{"name":"Jane"}' "user users"
cache_set_with_tags "post:1" '{"title":"Hello"}' "post posts user:1000"

# Invalidate all user caches
cache_invalidate_by_tag "users"

# Cache with dependencies
cache_set_with_dependencies() {
  local key=$1
  local value=$2
  shift 2
  local dependencies=("$@")

  # Set cache
  cache_set "$key" "$value"

  # Track dependencies
  for dep in "${dependencies[@]}"; do
    redis-cli SADD "cache:deps:$dep" "cache:$key"
  done
}

# Invalidate with dependencies
cache_invalidate_with_deps() {
  local key=$1

  # Get dependent caches
  local deps=$(redis-cli SMEMBERS "cache:deps:$key")

  # Invalidate all dependent caches
  for dep in $deps; do
    redis-cli DEL "$dep"
  done

  # Invalidate main key
  cache_invalidate "$key"

  redis-cli DEL "cache:deps:$key"
}

# Automatic cache warming
warm_popular_items() {
  # Get popular items (tracked separately)
  local popular=$(redis-cli ZREVRANGE "popular:items" 0 99)

  for item in $popular; do
    # Check if cached
    if ! cache_get "$item" > /dev/null; then
      # Fetch and cache
      local value=$(fetch_from_database "$item")
      cache_set "$item" "$value"
    fi
  done
}

# Cache hit rate monitoring
get_cache_hit_rate() {
  local stats=$(redis-cli HGETALL cache:stats)
  local hits=$(echo "$stats" | grep -A1 "hits" | tail -1)
  local misses=$(echo "$stats" | grep -A1 "misses" | tail -1)

  if [ -z "$hits" ] || [ -z "$misses" ]; then
    echo "No statistics available"
    return
  fi

  local total=$((hits + misses))
  if [ $total -eq 0 ]; then
    echo "No cache operations"
    return
  fi

  local hit_rate=$(echo "scale=2; $hits * 100 / $total" | bc)
  echo "Cache hit rate: $hit_rate%"
  echo "Hits: $hits, Misses: $misses, Total: $total"
}

# Test the caching system
echo "=== Testing Cache System ==="

# Test cache-aside
for i in {1..10}; do
  cache_get "test:$i" || cache_set "test:$i" "value$i"
done

# Test cache hits
for i in {1..10}; do
  cache_get "test:$i" > /dev/null
done

# Show statistics
echo -e "\n=== Cache Statistics ==="
get_cache_hit_rate

# Test tagged invalidation
cache_set_with_tags "product:1" '{"name":"Laptop"}' "products electronics"
cache_set_with_tags "product:2" '{"name":"Phone"}' "products electronics"
cache_set_with_tags "product:3" '{"name":"Desk"}' "products furniture"

echo -e "\n=== Before Tag Invalidation ==="
cache_get "product:1"
cache_get "product:2"

echo -e "\n=== After Tag Invalidation (electronics) ==="
cache_invalidate_by_tag "electronics"
cache_get "product:1"
cache_get "product:2"
cache_get "product:3"  # Should still be cached
```
</details>

---

## 9. Pub/Sub Messaging

**Time:** 30 minutes

### 9.1 Basic Pub/Sub

```bash
# Terminal 1: Subscribe to channel
SUBSCRIBE news

# Terminal 2: Publish message
PUBLISH news "Breaking news!"

# Subscribe to multiple channels
SUBSCRIBE news sports weather

# Unsubscribe
UNSUBSCRIBE news
```

### 9.2 Pattern Matching

```bash
# Subscribe to pattern
PSUBSCRIBE news.*
PSUBSCRIBE user:*:notifications

# Publish to matching channels
PUBLISH news.tech "Tech news"
PUBLISH news.sports "Sports news"
PUBLISH user:1000:notifications "You have a new message"
```

### 9.3 Pub/Sub Commands

```bash
# List active channels
PUBSUB CHANNELS

# Count subscribers
PUBSUB NUMSUB news sports

# Count pattern subscribers
PUBSUB NUMPAT
```

**Exercise 9.1:** Build a real-time notification system
- User notifications
- Chat room implementation
- Event broadcasting

<details>
<summary>Solution</summary>

```bash
# Real-time Notification System

# Subscriber script (notification-listener.sh)
cat > notification-listener.sh <<'EOF'
#!/bin/bash

user_id=$1

if [ -z "$user_id" ]; then
  echo "Usage: $0 <user_id>"
  exit 1
fi

echo "Listening for notifications for user $user_id..."

redis-cli SUBSCRIBE "user:$user_id:notifications" | while read -r line; do
  if [[ $line =~ ^message ]]; then
    # Extract message
    read -r channel
    read -r message
    echo "[$(date '+%H:%M:%S')] Notification: $message"
  fi
done
EOF

chmod +x notification-listener.sh

# Publisher script
send_notification() {
  local user_id=$1
  local message=$2

  redis-cli PUBLISH "user:$user_id:notifications" "$message"

  # Also store in history
  redis-cli LPUSH "user:$user_id:notification_history" "{\"message\":\"$message\",\"time\":\"$(date -Iseconds)\"}"
  redis-cli LTRIM "user:$user_id:notification_history" 0 99  # Keep last 100
}

# Test notifications
send_notification 1000 "You have a new follower"
send_notification 1000 "Your post was liked"

# Chat Room Implementation

# Join chat room (subscriber)
cat > chat-client.sh <<'EOF'
#!/bin/bash

room=$1
username=$2

if [ -z "$room" ] || [ -z "$username" ]; then
  echo "Usage: $0 <room> <username>"
  exit 1
fi

echo "Joined chat room: $room as $username"
echo "Type messages and press Enter to send"

# Subscribe to chat in background
redis-cli SUBSCRIBE "chat:$room" | while read -r line; do
  if [[ $line =~ ^message ]]; then
    read -r channel
    read -r message
    # Don't show own messages
    if [[ ! $message =~ ^\[$username\] ]]; then
      echo "$message"
    fi
  fi
done &

# Send messages
while read -r message; do
  if [ -n "$message" ]; then
    redis-cli PUBLISH "chat:$room" "[$username] $message"

    # Store in chat history
    redis-cli LPUSH "chat:$room:history" "[$username] $message"
    redis-cli LTRIM "chat:$room:history" 0 999
  fi
done
EOF

chmod +x chat-client.sh

# Event Broadcasting

# Broadcaster
broadcast_event() {
  local event_type=$1
  shift
  local data="$@"

  local timestamp=$(date -Iseconds)
  local event_json="{\"type\":\"$event_type\",\"data\":\"$data\",\"timestamp\":\"$timestamp\"}"

  # Broadcast to all subscribers
  redis-cli PUBLISH "events:$event_type" "$event_json"

  # Also publish to global channel
  redis-cli PUBLISH "events:all" "$event_json"

  # Store in event log
  redis-cli ZADD "events:log" $(date +%s) "$event_json"
}

# Event listener
cat > event-listener.sh <<'EOF'
#!/bin/bash

event_types=$@

if [ -z "$event_types" ]; then
  echo "Usage: $0 <event_type1> [event_type2] ..."
  exit 1
fi

channels=""
for event in $event_types; do
  channels="$channels events:$event"
done

echo "Listening for events: $event_types"

redis-cli SUBSCRIBE $channels | while read -r line; do
  if [[ $line =~ ^message ]]; then
    read -r channel
    read -r message
    echo "[$(date '+%H:%M:%S')] $channel: $message"
  fi
done
EOF

chmod +x event-listener.sh

# Test event broadcasting
broadcast_event "user_registered" "New user: john@example.com"
broadcast_event "order_placed" "Order #1234"
broadcast_event "payment_received" "Payment for order #1234"

# Pattern-based subscription for monitoring
redis-cli PSUBSCRIBE "events:*" | while read -r line; do
  if [[ $line =~ ^pmessage ]]; then
    read -r pattern
    read -r channel
    read -r message
    echo "[Monitor] $channel: $message"
  fi
done &

# Real-time Analytics Dashboard

# Track online users
user_online() {
  local user_id=$1

  redis-cli SETEX "online:$user_id" 300 "1"  # 5 minute timeout
  redis-cli PUBLISH "events:user_status" "{\"user\":\"$user_id\",\"status\":\"online\"}"
}

user_offline() {
  local user_id=$1

  redis-cli DEL "online:$user_id"
  redis-cli PUBLISH "events:user_status" "{\"user\":\"$user_id\",\"status\":\"offline\"}"
}

# Get online user count
get_online_count() {
  redis-cli KEYS "online:*" | wc -l
}

# Presence system with heartbeat
keep_alive() {
  local user_id=$1

  while true; do
    redis-cli SETEX "online:$user_id" 300 "1"
    sleep 60
  done
}

# Subscribe to presence updates
redis-cli SUBSCRIBE "events:user_status" | while read -r line; do
  if [[ $line =~ ^message ]]; then
    read -r channel
    read -r message
    echo "User status changed: $message"

    # Update dashboard
    online_count=$(get_online_count)
    echo "Currently online: $online_count users"
  fi
done
```
</details>

---

## 10. Transactions and Pipelining

**Time:** 30 minutes

### 10.1 Transactions (MULTI/EXEC)

```bash
# Basic transaction
MULTI
SET key1 "value1"
SET key2 "value2"
INCR counter
EXEC

# Transaction with discard
MULTI
SET key1 "value1"
DISCARD

# Watch for changes (optimistic locking)
WATCH balance
MULTI
DECRBY balance 100
EXEC
```

### 10.2 Pipelining

```bash
# Using redis-cli pipeline
cat commands.txt | redis-cli --pipe

# Example commands.txt:
SET key1 "value1"
SET key2 "value2"
INCR counter
GET key1
```

### 10.3 Lua Scripts (Atomic Operations)

```bash
# Increment if exists
redis-cli --eval - mykey 10 <<'EOF'
local key = KEYS[1]
local increment = tonumber(ARGV[1])

if redis.call('EXISTS', key) == 1 then
  return redis.call('INCRBY', key, increment)
else
  return nil
end
EOF

# Rate limiting script
redis-cli --eval rate-limit.lua user:1000 60 10
```

**Exercise 10.1:** Implement atomic operations
- Bank transfer with transactions
- Inventory management
- Distributed locking

<details>
<summary>Solution</summary>

```bash
# Bank Transfer with Transactions

transfer_money() {
  local from_account=$1
  local to_account=$2
  local amount=$3

  redis-cli --eval - $from_account $to_account $amount <<'EOF'
local from = KEYS[1]
local to = KEYS[2]
local amount = tonumber(ARGV[1])

-- Check balance
local balance = tonumber(redis.call('GET', from) or 0)

if balance < amount then
  return redis.error_reply("Insufficient funds")
end

-- Perform transfer
redis.call('DECRBY', from, amount)
redis.call('INCRBY', to, amount)

-- Log transaction
local txn = string.format('{"from":"%s","to":"%s","amount":%d,"time":%d}',
  from, to, amount, redis.call('TIME')[1])
redis.call('LPUSH', 'transactions:log', txn)

return redis.status_reply("OK")
EOF
}

# Setup accounts
redis-cli SET account:1000 1000
redis-cli SET account:2000 500

# Test transfer
transfer_money account:1000 account:2000 100

# Inventory Management (prevent overselling)

reserve_inventory() {
  local product_id=$1
  local quantity=$2

  redis-cli --eval - $product_id $quantity <<'EOF'
local product = KEYS[1]
local qty = tonumber(ARGV[1])

-- Get current inventory
local current = tonumber(redis.call('HGET', 'inventory', product) or 0)

if current < qty then
  return redis.error_reply("Insufficient inventory")
end

-- Reserve inventory
redis.call('HINCRBY', 'inventory', product, -qty)
redis.call('HINCRBY', 'inventory:reserved', product, qty)

return redis.status_reply("OK")
EOF
}

# Release inventory (if order cancelled)
release_inventory() {
  local product_id=$1
  local quantity=$2

  redis-cli --eval - $product_id $quantity <<'EOF'
local product = KEYS[1]
local qty = tonumber(ARGV[1])

redis.call('HINCRBY', 'inventory', product, qty)
redis.call('HINCRBY', 'inventory:reserved', product, -qty)

return redis.status_reply("OK")
EOF
}

# Setup inventory
redis-cli HSET inventory prod:1 100 prod:2 50 prod:3 25

# Test inventory operations
reserve_inventory prod:1 10
release_inventory prod:1 5

# Distributed Locking

acquire_lock() {
  local resource=$1
  local lock_id=$2
  local ttl=${3:-30}

  # SET NX EX pattern
  redis-cli SET "lock:$resource" "$lock_id" NX EX $ttl
}

release_lock() {
  local resource=$1
  local lock_id=$2

  # Only release if we own the lock
  redis-cli --eval - "lock:$resource" $lock_id <<'EOF'
local key = KEYS[1]
local expected_id = ARGV[1]

if redis.call('GET', key) == expected_id then
  return redis.call('DEL', key)
else
  return 0
end
EOF
}

# Extend lock
extend_lock() {
  local resource=$1
  local lock_id=$2
  local ttl=$3

  redis-cli --eval - "lock:$resource" $lock_id $ttl <<'EOF'
local key = KEYS[1]
local expected_id = ARGV[1]
local ttl = tonumber(ARGV[2])

if redis.call('GET', key) == expected_id then
  return redis.call('EXPIRE', key, ttl)
else
  return 0
end
EOF
}

# Usage example
lock_id=$(uuidgen)
if acquire_lock "resource1" "$lock_id" 30; then
  echo "Lock acquired"

  # Do work
  sleep 5

  # Release lock
  if release_lock "resource1" "$lock_id"; then
    echo "Lock released"
  fi
else
  echo "Failed to acquire lock"
fi

# Redlock (distributed lock across multiple Redis instances)
acquire_redlock() {
  local resource=$1
  local lock_id=$2
  local ttl=$3
  local instances=("$@:4")

  local acquired=0
  local required=$((${#instances[@]} / 2 + 1))

  for instance in "${instances[@]}"; do
    if redis-cli -h $instance SET "lock:$resource" "$lock_id" NX EX $ttl; then
      ((acquired++))
    fi
  done

  if [ $acquired -ge $required ]; then
    return 0
  else
    # Release acquired locks
    for instance in "${instances[@]}"; do
      redis-cli -h $instance --eval - "lock:$resource" $lock_id <<'EOF'
if redis.call('GET', KEYS[1]) == ARGV[1] then
  return redis.call('DEL', KEYS[1])
end
EOF
    done
    return 1
  fi
}

# Atomic counter with limit
increment_with_limit() {
  local key=$1
  local increment=$2
  local max_value=$3

  redis-cli --eval - $key $increment $max_value <<'EOF'
local key = KEYS[1]
local increment = tonumber(ARGV[1])
local max_value = tonumber(ARGV[2])

local current = tonumber(redis.call('GET', key) or 0)

if current + increment > max_value then
  return redis.error_reply("Would exceed maximum value")
end

return redis.call('INCRBY', key, increment)
EOF
}

# Idempotent operation
execute_once() {
  local operation_id=$1
  local operation=$2

  redis-cli --eval - $operation_id <<'EOF'
local op_id = KEYS[1]

-- Check if already executed
if redis.call('EXISTS', 'executed:' .. op_id) == 1 then
  return redis.error_reply("Operation already executed")
end

-- Mark as executed (1 hour TTL)
redis.call('SET EX', 'executed:' .. op_id, 3600, '1')

return redis.status_reply("OK")
EOF

  if [ $? -eq 0 ]; then
    eval "$operation"
  fi
}

# Usage
execute_once "op-12345" "echo 'Processing payment'"
execute_once "op-12345" "echo 'Processing payment'"  # Will be rejected
```
</details>

---

## 11. Persistence and Durability

**Time:** 30 minutes

### 11.1 RDB (Snapshotting)

```bash
# Configure RDB
CONFIG SET save "900 1 300 10 60 10000"

# Manual snapshot
SAVE      # Blocking
BGSAVE    # Background

# Get last save time
LASTSAVE

# Check if save is in progress
INFO persistence | grep rdb_bgsave_in_progress
```

### 11.2 AOF (Append-Only File)

```bash
# Enable AOF
CONFIG SET appendonly yes
CONFIG SET appendfsync everysec

# Rewrite AOF
BGREWRITEAOF

# Check AOF status
INFO persistence | grep aof
```

### 11.3 Persistence Strategies

```bash
# No persistence (cache only)
CONFIG SET save ""
CONFIG SET appendonly no

# RDB only (snapshots)
CONFIG SET save "900 1 300 10 60 10000"
CONFIG SET appendonly no

# AOF only (durability)
CONFIG SET save ""
CONFIG SET appendonly yes
CONFIG SET appendfsync everysec

# Both RDB and AOF (recommended)
CONFIG SET save "900 1 300 10"
CONFIG SET appendonly yes
CONFIG SET appendfsync everysec
```

**Exercise 11.1:** Configure and test persistence
- Set up RDB with custom intervals
- Enable AOF with fsync policy
- Simulate crash and recovery
- Measure performance impact

<details>
<summary>Solution</summary>

```bash
# Persistence Configuration Script

configure_persistence() {
  echo "Configuring Redis persistence..."

  # RDB configuration
  redis-cli CONFIG SET save "900 1 300 10 60 10000"
  redis-cli CONFIG SET stop-writes-on-bgsave-error yes
  redis-cli CONFIG SET rdbcompression yes
  redis-cli CONFIG SET rdbchecksum yes
  redis-cli CONFIG SET dbfilename dump.rdb

  # AOF configuration
  redis-cli CONFIG SET appendonly yes
  redis-cli CONFIG SET appendfilename "appendonly.aof"
  redis-cli CONFIG SET appendfsync everysec
  redis-cli CONFIG SET no-appendfsync-on-rewrite no
  redis-cli CONFIG SET auto-aof-rewrite-percentage 100
  redis-cli CONFIG SET auto-aof-rewrite-min-size 64mb

  # Save configuration
  redis-cli CONFIG REWRITE

  echo "Persistence configured successfully"
}

# Test persistence
test_persistence() {
  echo "Testing persistence..."

  # Add test data
  for i in {1..1000}; do
    redis-cli SET "persist:test:$i" "value$i" > /dev/null
  done

  echo "Added 1000 keys"

  # Force save
  redis-cli BGSAVE

  # Wait for save to complete
  while [ "$(redis-cli INFO persistence | grep rdb_bgsave_in_progress | cut -d: -f2 | tr -d '\r')" == "1" ]; do
    sleep 1
  done

  echo "RDB save completed"

  # Force AOF rewrite
  redis-cli BGREWRITEAOF

  echo "AOF rewrite triggered"

  # Show persistence stats
  echo -e "\n=== Persistence Statistics ==="
  redis-cli INFO persistence
}

# Simulate crash and recovery
simulate_crash_recovery() {
  echo "Simulating crash and recovery..."

  # Add data
  redis-cli SET crash:test:1 "before crash"
  redis-cli SET crash:test:2 "before crash"

  # Force save
  redis-cli SAVE

  # Add more data (not saved)
  redis-cli SET crash:test:3 "after save"

  # Get current data
  echo "Before crash:"
  redis-cli MGET crash:test:1 crash:test:2 crash:test:3

  # Simulate crash (restart container)
  docker restart my-redis

  # Wait for Redis to start
  sleep 5

  # Check recovered data
  echo "After recovery:"
  redis-cli MGET crash:test:1 crash:test:2 crash:test:3
}

# Measure persistence performance
measure_persistence_performance() {
  echo "Measuring persistence performance..."

  # Benchmark without persistence
  redis-cli CONFIG SET save ""
  redis-cli CONFIG SET appendonly no

  echo "Benchmark WITHOUT persistence:"
  redis-benchmark -t set,get -n 100000 -q

  # Enable persistence
  redis-cli CONFIG SET save "900 1"
  redis-cli CONFIG SET appendonly yes

  echo -e "\nBenchmark WITH persistence:"
  redis-benchmark -t set,get -n 100000 -q

  # Reset
  redis-cli CONFIG SET save "900 1 300 10 60 10000"
}

# Monitor persistence
monitor_persistence() {
  while true; do
    clear
    echo "=== Redis Persistence Monitor ==="
    echo "Time: $(date)"
    echo ""

    # RDB info
    echo "--- RDB Snapshot ---"
    redis-cli INFO persistence | grep -E "rdb_last_save_time|rdb_last_bgsave_status|rdb_last_bgsave_time_sec|rdb_current_bgsave_time_sec"

    echo ""

    # AOF info
    echo "--- AOF ---"
    redis-cli INFO persistence | grep -E "aof_enabled|aof_last_rewrite_time_sec|aof_current_rewrite_time_sec|aof_buffer_length|aof_rewrite_in_progress"

    echo ""

    # File sizes
    echo "--- File Sizes ---"
    docker exec my-redis sh -c "du -h /data/*.rdb /data/*.aof 2>/dev/null || echo 'No persistence files yet'"

    sleep 5
  done
}

# Backup persistence files
backup_persistence_files() {
  local backup_dir="/backups/redis/$(date +%Y%m%d_%H%M%S)"

  mkdir -p $backup_dir

  # Copy RDB file
  docker cp my-redis:/data/dump.rdb $backup_dir/

  # Copy AOF file
  docker cp my-redis:/data/appendonly.aof $backup_dir/

  echo "Persistence files backed up to $backup_dir"
}

# Restore from backup
restore_from_backup() {
  local backup_dir=$1

  if [ ! -d "$backup_dir" ]; then
    echo "Backup directory not found: $backup_dir"
    exit 1
  fi

  # Stop Redis
  docker stop my-redis

  # Restore files
  docker cp $backup_dir/dump.rdb my-redis:/data/
  docker cp $backup_dir/appendonly.aof my-redis:/data/

  # Start Redis
  docker start my-redis

  echo "Restored from backup: $backup_dir"
}

# Run configuration
configure_persistence

# Run tests
test_persistence
```
</details>

---

## 12. Performance and Optimization

**Time:** 30 minutes

### 12.1 Performance Monitoring

```bash
# Server info
INFO
INFO stats
INFO memory
INFO cpu

# Monitor commands in real-time
MONITOR

# Slow log
SLOWLOG GET 10
SLOWLOG LEN
SLOWLOG RESET

# Configure slow log
CONFIG SET slowlog-log-slower-than 10000  # microseconds
CONFIG SET slowlog-max-len 128

# Memory usage
MEMORY USAGE key
MEMORY STATS
MEMORY DOCTOR

# Client list
CLIENT LIST
CLIENT KILL ip:port
```

### 12.2 Optimization Tips

```bash
# Use pipelines for bulk operations
cat commands.txt | redis-cli --pipe

# Use SCAN instead of KEYS
SCAN 0 MATCH "user:*" COUNT 100

# Set appropriate maxmemory and eviction policy
CONFIG SET maxmemory 2gb
CONFIG SET maxmemory-policy allkeys-lru

# Use connection pooling in applications

# Optimize data structures
# - Use hashes for objects
# - Use sorted sets for leaderboards
# - Use bitmaps for flags

# Enable lazy freeing
CONFIG SET lazyfree-lazy-eviction yes
CONFIG SET lazyfree-lazy-expire yes
```

### 12.3 Memory Optimization

```bash
# Find biggest keys
redis-cli --bigkeys

# Memory usage by key pattern
redis-cli --memkeys --memkeys-samples 10000

# Optimize hash encoding
CONFIG SET hash-max-ziplist-entries 512
CONFIG SET hash-max-ziplist-value 64
```

**Exercise 12.1:** Performance tuning and monitoring
- Identify slow queries
- Optimize memory usage
- Tune configuration
- Create monitoring dashboard

<details>
<summary>Solution</summary>

```bash
#!/bin/bash
# redis-performance-tuning.sh

# Performance analysis
analyze_performance() {
  echo "=== Redis Performance Analysis ==="

  # Get server info
  echo -e "\n--- Server Info ---"
  redis-cli INFO server | grep -E "redis_version|os|arch_bits|multiplexing_api|gcc_version"

  # Memory usage
  echo -e "\n--- Memory Usage ---"
  redis-cli INFO memory | grep -E "used_memory_human|used_memory_peak_human|mem_fragmentation_ratio|maxmemory_human|maxmemory_policy"

  # Stats
  echo -e "\n--- Statistics ---"
  redis-cli INFO stats | grep -E "total_connections_received|total_commands_processed|instantaneous_ops_per_sec|keyspace_hits|keyspace_misses"

  # Calculate hit rate
  local hits=$(redis-cli INFO stats | grep keyspace_hits | cut -d: -f2 | tr -d '\r')
  local misses=$(redis-cli INFO stats | grep keyspace_misses | cut -d: -f2 | tr -d '\r')
  if [ -n "$hits" ] && [ -n "$misses" ]; then
    local total=$((hits + misses))
    if [ $total -gt 0 ]; then
      local hit_rate=$(echo "scale=2; $hits * 100 / $total" | bc)
      echo "Cache hit rate: $hit_rate%"
    fi
  fi

  # CPU usage
  echo -e "\n--- CPU Usage ---"
  redis-cli INFO cpu

  # Slow log
  echo -e "\n--- Slow Queries (last 10) ---"
  redis-cli SLOWLOG GET 10

  # Biggest keys
  echo -e "\n--- Biggest Keys ---"
  redis-cli --bigkeys

  # Connected clients
  echo -e "\n--- Connected Clients ---"
  redis-cli CLIENT LIST | wc -l
}

# Optimize configuration
optimize_config() {
  echo "Optimizing Redis configuration..."

  # Memory management
  redis-cli CONFIG SET maxmemory 2gb
  redis-cli CONFIG SET maxmemory-policy allkeys-lru
  redis-cli CONFIG SET maxmemory-samples 5

  # Lazy freeing
  redis-cli CONFIG SET lazyfree-lazy-eviction yes
  redis-cli CONFIG SET lazyfree-lazy-expire yes
  redis-cli CONFIG SET lazyfree-lazy-server-del yes

  # Slow log
  redis-cli CONFIG SET slowlog-log-slower-than 10000
  redis-cli CONFIG SET slowlog-max-len 128

  # Networking
  redis-cli CONFIG SET tcp-backlog 511
  redis-cli CONFIG SET timeout 300

  # Persistence (if needed)
  redis-cli CONFIG SET save "900 1 300 10 60 10000"
  redis-cli CONFIG SET stop-writes-on-bgsave-error no

  # Save configuration
  redis-cli CONFIG REWRITE

  echo "Configuration optimized"
}

# Memory analysis
analyze_memory() {
  echo "=== Memory Analysis ==="

  # Overall memory usage
  redis-cli INFO memory

  # Sample key memory usage
  echo -e "\n--- Sample Key Memory Usage ---"
  for key in $(redis-cli --scan --count 100 | head -20); do
    size=$(redis-cli MEMORY USAGE $key)
    echo "$key: $size bytes"
  done

  # Memory doctor
  echo -e "\n--- Memory Doctor ---"
  redis-cli MEMORY DOCTOR
}

# Real-time monitoring dashboard
monitoring_dashboard() {
  while true; do
    clear
    echo "=== Redis Real-Time Monitor ==="
    echo "Time: $(date '+%H:%M:%S')"
    echo ""

    # Ops per second
    ops=$(redis-cli INFO stats | grep instantaneous_ops_per_sec | cut -d: -f2 | tr -d '\r')
    echo "Operations/sec: $ops"

    # Memory
    used_mem=$(redis-cli INFO memory | grep used_memory_human | cut -d: -f2 | tr -d '\r')
    echo "Memory used: $used_mem"

    # Hit rate
    hits=$(redis-cli INFO stats | grep keyspace_hits | cut -d: -f2 | tr -d '\r')
    misses=$(redis-cli INFO stats | grep keyspace_misses | cut -d: -f2 | tr -d '\r')
    if [ -n "$hits" ] && [ -n "$misses" ]; then
      total=$((hits + misses))
      if [ $total -gt 0 ]; then
        hit_rate=$(echo "scale=2; $hits * 100 / $total" | bc)
        echo "Cache hit rate: $hit_rate%"
      fi
    fi

    # Connected clients
    clients=$(redis-cli CLIENT LIST | wc -l)
    echo "Connected clients: $clients"

    # Keys
    keys=$(redis-cli DBSIZE)
    echo "Total keys: $keys"

    # Latest slow query
    echo -e "\n--- Latest Slow Query ---"
    redis-cli SLOWLOG GET 1

    sleep 2
  done
}

# Benchmark
run_benchmark() {
  echo "Running Redis benchmark..."

  redis-benchmark -t set,get,incr,lpush,rpush,lpop,rpop,sadd,hset,spop,zadd,zpopmin,lrange,mset -n 100000 -q

  echo -e "\n\nRunning pipeline benchmark..."
  redis-benchmark -t set,get -P 16 -n 100000 -q
}

# Main menu
show_menu() {
  echo "=== Redis Performance Tools ==="
  echo "1. Analyze performance"
  echo "2. Optimize configuration"
  echo "3. Analyze memory"
  echo "4. Real-time monitoring"
  echo "5. Run benchmark"
  echo "6. Exit"
  read -p "Select option: " option

  case $option in
    1) analyze_performance ;;
    2) optimize_config ;;
    3) analyze_memory ;;
    4) monitoring_dashboard ;;
    5) run_benchmark ;;
    6) exit 0 ;;
    *) echo "Invalid option" ;;
  esac

  echo -e "\nPress Enter to continue..."
  read
  show_menu
}

# Run menu
show_menu
```
</details>

---

## 13. Real-World Use Cases

**Time:** 45 minutes

### Use Case 1: Session Store

```bash
# Create session
SESSION_ID=$(uuidgen)
redis-cli SETEX "session:$SESSION_ID" 3600 '{"user_id":1000,"username":"john","email":"john@example.com"}'

# Get session
redis-cli GET "session:$SESSION_ID"

# Update session
redis-cli SETEX "session:$SESSION_ID" 3600 '{"user_id":1000,"username":"john","email":"john@example.com","last_activity":"2024-01-15T10:30:00Z"}'

# Delete session (logout)
redis-cli DEL "session:$SESSION_ID"
```

### Use Case 2: Rate Limiting

```bash
# Simple rate limiter (10 requests per minute)
check_rate_limit() {
  local user_id=$1
  local key="ratelimit:$user_id:$(date +%Y%m%d%H%M)"

  local count=$(redis-cli INCR $key)
  redis-cli EXPIRE $key 60

  if [ $count -le 10 ]; then
    echo "allowed"
  else
    echo "rate_limited"
  fi
}
```

### Use Case 3: Leaderboard

```bash
# Add score
ZADD game:leaderboard 1500 "player1"
ZADD game:leaderboard 2000 "player2"

# Update score
ZINCRBY game:leaderboard 100 "player1"

# Get top 10
ZREVRANGE game:leaderboard 0 9 WITHSCORES

# Get player rank
ZREVRANK game:leaderboard "player1"
```

### Use Case 4: Real-time Analytics

```bash
# Page views
INCR page:home:views:$(date +%Y%m%d)
INCR page:home:views:total

# Unique visitors (HyperLogLog)
PFADD visitors:$(date +%Y%m%d) "user:1000"
PFCOUNT visitors:$(date +%Y%m%d)
```

---

## 14. Troubleshooting

### Common Issues

#### Issue 1: High Memory Usage

**Diagnosis:**
```bash
redis-cli INFO memory
redis-cli --bigkeys
MEMORY DOCTOR
```

**Solutions:**
- Set maxmemory and eviction policy
- Use appropriate data structures
- Set TTL on keys

#### Issue 2: Slow Performance

**Diagnosis:**
```bash
redis-cli SLOWLOG GET 10
redis-cli --latency
```

**Solutions:**
- Avoid KEYS command (use SCAN)
- Use pipelining
- Optimize data structures

#### Issue 3: Connection Issues

**Solutions:**
- Check maxclients setting
- Use connection pooling
- Monitor CLIENT LIST

---

## Conclusion

You've completed the Redis Complete Guide! You should now be able to:

✅ Set up and configure Redis
✅ Work with all Redis data types
✅ Implement caching strategies
✅ Build real-time features with Pub/Sub
✅ Optimize performance
✅ Handle persistence and backups

**Next Steps:**
1. Explore Redis Cluster for horizontal scaling
2. Learn about Redis Modules (RedisJSON, RediSearch, etc.)
3. Study Redis Streams for event sourcing
4. Practice with production workloads

Happy caching! ⚡
