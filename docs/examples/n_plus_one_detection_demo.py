#!/usr/bin/env python3
"""
N+1 Query Detection Demo

Demonstrates the N+1 query detection feature in the query optimizer.
"""

import json
import time
from pathlib import Path

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.database.query_optimizer import QueryOptimizer
from src.database.n_plus_one_detector import NPlusOneDetector


def create_example_query_log():
    """Create an example query log with N+1 pattern"""
    # Simulate a typical N+1 scenario:
    # 1. Fetch all users
    # 2. For each user, fetch their orders (N+1 problem!)

    query_log = []
    base_time = time.time() * 1000  # Convert to milliseconds

    # Initial query to get users
    query_log.append({
        'query': 'SELECT * FROM users LIMIT 20',
        'timestamp': base_time,
        'params': []
    })

    # N+1: Query for each user's orders (20 queries!)
    for i in range(1, 21):
        query_log.append({
            'query': f'SELECT * FROM orders WHERE user_id = {i}',
            'timestamp': base_time + (i * 10),  # 10ms between queries
            'params': [i]
        })

    return query_log


def demo_basic_detection():
    """Demo 1: Basic N+1 detection"""
    print("=" * 80)
    print("DEMO 1: Basic N+1 Query Detection")
    print("=" * 80)

    optimizer = QueryOptimizer(database_type='postgresql')
    query_log = create_example_query_log()

    print(f"\nAnalyzing {len(query_log)} queries from log...")
    suggestions = optimizer.analyze_query_log(query_log)

    if suggestions:
        print(f"\n✗ Found {len(suggestions)} optimization suggestion(s):\n")

        for i, suggestion in enumerate(suggestions, 1):
            print(f"Suggestion #{i}:")
            print(f"  Type: {suggestion.type.value}")
            print(f"  Level: {suggestion.level.value.upper()}")
            print(f"  Message: {suggestion.message}")
            print(f"  Improvement: {suggestion.estimated_improvement}")
            print(f"\n  Original Query:")
            print(f"    {suggestion.original_query}")
            print(f"\n  Suggested Fix:")
            for line in suggestion.suggested_query.split('\n'):
                print(f"    {line}")
            print(f"\n  Explanation:")
            for line in suggestion.explanation.split('\n'):
                print(f"    {line}")
            print(f"\n  Details:")
            for key, value in suggestion.details.items():
                if key == 'sample_params':
                    print(f"    {key}: {value[:3]}... (showing first 3)")
                else:
                    print(f"    {key}: {value}")
            print()
    else:
        print("\n✓ No N+1 patterns detected!")


def demo_custom_thresholds():
    """Demo 2: Custom detection thresholds"""
    print("=" * 80)
    print("DEMO 2: Custom Detection Thresholds")
    print("=" * 80)

    # Create smaller N+1 pattern (7 queries)
    query_log = []
    base_time = time.time() * 1000

    for i in range(1, 8):
        query_log.append({
            'query': f'SELECT * FROM orders WHERE user_id = {i}',
            'timestamp': base_time + (i * 5),
            'params': [i]
        })

    # Default detector (threshold=10) - should NOT detect
    optimizer = QueryOptimizer()
    suggestions = optimizer.detect_n_plus_one(query_log)

    print(f"\nWith default threshold (10 queries):")
    print(f"  Queries in log: {len(query_log)}")
    print(f"  Detected patterns: {len(suggestions)}")

    # Custom detector (threshold=5) - SHOULD detect
    suggestions = optimizer.detect_n_plus_one(
        query_log,
        threshold=5
    )

    print(f"\nWith custom threshold (5 queries):")
    print(f"  Queries in log: {len(query_log)}")
    print(f"  Detected patterns: {len(suggestions)}")

    if suggestions:
        print(f"\n  ✓ N+1 pattern detected with lower threshold!")


def demo_real_world_scenario():
    """Demo 3: Real-world scenario with mixed queries"""
    print("\n" + "=" * 80)
    print("DEMO 3: Real-World Scenario (Mixed Queries)")
    print("=" * 80)

    query_log = []
    base_time = time.time() * 1000

    # Some normal queries
    query_log.extend([
        {
            'query': 'SELECT COUNT(*) FROM users',
            'timestamp': base_time,
            'params': []
        },
        {
            'query': 'SELECT * FROM products WHERE category = "electronics" LIMIT 10',
            'timestamp': base_time + 50,
            'params': ['electronics']
        }
    ])

    # N+1 pattern: Load user profiles
    for i in range(1, 16):
        query_log.append({
            'query': f'SELECT * FROM user_profiles WHERE user_id = {i}',
            'timestamp': base_time + 100 + (i * 8),
            'params': [i]
        })

    # Another N+1 pattern: Load product reviews
    for i in range(1, 13):
        query_log.append({
            'query': f'SELECT * FROM reviews WHERE product_id = {i}',
            'timestamp': base_time + 400 + (i * 6),
            'params': [i]
        })

    # More normal queries
    query_log.extend([
        {
            'query': 'UPDATE cart SET updated_at = NOW() WHERE session_id = "abc123"',
            'timestamp': base_time + 600,
            'params': ['abc123']
        }
    ])

    optimizer = QueryOptimizer()
    suggestions = optimizer.analyze_query_log(query_log)

    print(f"\nAnalyzed {len(query_log)} queries from production-like log")
    print(f"Detected {len(suggestions)} N+1 pattern(s):")

    for i, suggestion in enumerate(suggestions, 1):
        print(f"\n  Pattern #{i}:")
        print(f"    Count: {suggestion.details['pattern_count']} queries")
        print(f"    Table: {suggestion.details['table']}")
        print(f"    Time window: {suggestion.details['time_window_ms']:.1f}ms")
        print(f"    Sample query: {suggestion.original_query}")


def demo_performance():
    """Demo 4: Performance with large query logs"""
    print("\n" + "=" * 80)
    print("DEMO 4: Performance Test with Large Query Log")
    print("=" * 80)

    # Generate large query log (500 queries)
    query_log = []
    base_time = time.time() * 1000

    # Multiple N+1 patterns
    for pattern in range(5):
        offset = pattern * 1000
        for i in range(100):
            query_log.append({
                'query': f'SELECT * FROM table_{pattern} WHERE id = {i}',
                'timestamp': base_time + offset + (i * 2),
                'params': [i]
            })

    optimizer = QueryOptimizer()

    print(f"\nAnalyzing {len(query_log)} queries...")

    start = time.time()
    suggestions = optimizer.analyze_query_log(query_log)
    duration = time.time() - start

    print(f"  Analysis completed in {duration*1000:.2f}ms")
    print(f"  Detected {len(suggestions)} N+1 pattern(s)")
    print(f"  Average time per query: {(duration/len(query_log))*1000:.3f}ms")

    if duration < 1.0:
        print(f"\n  ✓ Performance: Excellent (< 1 second)")
    elif duration < 2.0:
        print(f"\n  ✓ Performance: Good (< 2 seconds)")
    else:
        print(f"\n  ⚠ Performance: Could be improved")


def demo_save_and_load():
    """Demo 5: Save query log and analyze from file"""
    print("\n" + "=" * 80)
    print("DEMO 5: Save Query Log and Analyze from File")
    print("=" * 80)

    # Create example log
    query_log = create_example_query_log()

    # Save to file
    log_file = '/tmp/example_query_log.json'
    with open(log_file, 'w') as f:
        json.dump(query_log, f, indent=2)

    print(f"\n✓ Saved {len(query_log)} queries to {log_file}")

    # Load and analyze
    optimizer = QueryOptimizer()
    suggestions = optimizer.analyze_query_log_file(log_file)

    print(f"✓ Loaded and analyzed query log from file")
    print(f"✓ Found {len(suggestions)} optimization suggestion(s)")


def main():
    """Run all demos"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "N+1 Query Detection Demo".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "=" * 78 + "╝")
    print()

    try:
        demo_basic_detection()
        demo_custom_thresholds()
        demo_real_world_scenario()
        demo_performance()
        demo_save_and_load()

        print("\n" + "=" * 80)
        print("All demos completed successfully!")
        print("=" * 80 + "\n")

    except Exception as e:
        print(f"\n✗ Error during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
