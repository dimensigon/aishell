"""
Cognitive Features Integration Example

Demonstrates how Cognitive Memory, Anomaly Detection, and Autonomous DevOps
work together to create an intelligent, self-optimizing system.
"""

import asyncio
from pathlib import Path
from src.cognitive.memory import CognitiveMemory
from src.cognitive.anomaly_detector import AnomalyDetector, MetricCollector
from src.cognitive.autonomous_devops import AutonomousDevOps


async def example_1_memory_learning():
    """
    Example 1: Cognitive Memory learns from command patterns
    """
    print("=" * 60)
    print("Example 1: Cognitive Memory Learning")
    print("=" * 60)

    memory_dir = str(Path.home() / ".aishell" / "memory")
    memory = CognitiveMemory(memory_dir=memory_dir)

    # Simulate a development workflow
    print("\n📝 Recording development workflow...")

    commands = [
        ("cd /project/api", "Changed directory", None, {"cwd": "/"}, 0.1),
        ("git pull origin main", "Already up to date", None, {"cwd": "/project/api"}, 0.5),
        ("npm install", "added 245 packages", None, {"cwd": "/project/api"}, 12.3),
        ("npm test", "All tests passed", None, {"cwd": "/project/api"}, 8.7),
        ("git add .", "Files staged", None, {"cwd": "/project/api"}, 0.2),
        ("git commit -m 'feat: add new API endpoint'", "1 file changed", None, {"cwd": "/project/api"}, 0.3),
        ("git push origin main", "Pushed successfully", None, {"cwd": "/project/api"}, 1.2),
    ]

    for cmd, output, error, context, duration in commands:
        await memory.remember(cmd, output, error, context, duration)
        print(f"  ✓ Remembered: {cmd}")

    # Now recall similar commands
    print("\n🔍 Recalling git workflow...")
    git_memories = await memory.recall("git commit", k=3)

    for mem in git_memories:
        print(f"  • {mem.command} (importance: {mem.importance:.2f}, freq: {mem.frequency})")

    # Get command suggestions based on context
    print("\n💡 Getting suggestions for git workflow...")
    context = {"cwd": "/project/api", "last_command": "git add ."}
    suggestions = await memory.get_command_suggestions(context, k=3)

    for cmd, confidence in suggestions:
        print(f"  • {cmd} (confidence: {confidence:.0%})")

    # Get insights
    print("\n📊 Memory Insights:")
    insights = await memory.get_insights()
    print(f"  • Total memories: {insights['total_memories']}")
    print(f"  • Success rate: {insights['overall_success_rate']:.1%}")
    print(f"  • Most used commands:")
    for cmd_info in insights['most_used_commands'][:3]:
        print(f"    - {cmd_info['command']} ({cmd_info['count']} times)")


async def example_2_anomaly_detection_with_memory():
    """
    Example 2: Anomaly Detection using Cognitive Memory for pattern analysis
    """
    print("\n\n" + "=" * 60)
    print("Example 2: Anomaly Detection with Memory Integration")
    print("=" * 60)

    memory_dir = str(Path.home() / ".aishell" / "memory")
    memory = CognitiveMemory(memory_dir=memory_dir)

    collector = MetricCollector()
    detector = AnomalyDetector(memory=memory, auto_fix_enabled=True)

    print("\n🔍 Collecting system metrics...")
    metrics = await collector.collect()

    for metric_name, metric in metrics.items():
        print(f"  • {metric_name}: {metric.value:.2f} (threshold: {metric.threshold:.2f})")

    print("\n🚨 Detecting anomalies...")
    anomalies = await detector.detect_anomalies(metrics)

    if anomalies:
        print(f"  Found {len(anomalies)} anomalies:")
        for anomaly in anomalies:
            print(f"  • {anomaly.type.value}: {anomaly.description}")
            print(f"    Severity: {anomaly.severity.value}")

            # Attempt auto-remediation
            print(f"    Attempting auto-fix...")
            success = await detector.attempt_auto_remediation(anomaly)
            if success:
                print(f"    ✅ Auto-fix successful!")
                # Memory learns from successful remediation
                await memory.remember(
                    f"auto-fix: {anomaly.type.value}",
                    f"Fixed {anomaly.description}",
                    None,
                    {"anomaly_type": anomaly.type.value, "severity": anomaly.severity.value},
                    0.5
                )
            else:
                print(f"    ❌ Auto-fix failed")
    else:
        print("  ✅ No anomalies detected!")

    # Check detector status
    status = await detector.get_status()
    print(f"\n📈 Detector Status:")
    print(f"  • Active anomalies: {status['active_anomalies']}")
    print(f"  • Auto-fixes applied: {status['auto_fixes_applied']}")
    print(f"  • Fixes remaining this hour: {status['fixes_remaining_this_hour']}/10")


async def example_3_autonomous_devops_with_learning():
    """
    Example 3: Autonomous DevOps learns from past optimizations
    """
    print("\n\n" + "=" * 60)
    print("Example 3: Autonomous DevOps with Learning")
    print("=" * 60)

    memory_dir = str(Path.home() / ".aishell" / "memory")
    memory = CognitiveMemory(memory_dir=memory_dir)
    ada = AutonomousDevOps(memory=memory)

    print("\n🔍 Analyzing infrastructure...")
    state = await ada.analyze_infrastructure()

    print(f"\n📊 Infrastructure State:")
    print(f"  • Services: {len(state.services)}")
    if state.services:
        for service in state.services[:3]:
            print(f"    - {service['name']}: {service['instances']} instances")
            print(f"      CPU: {service['cpu_usage']:.1f}%, Memory: {service['memory_usage']:.1f}%")

    if state.costs:
        print(f"\n💰 Cost Analysis:")
        print(f"  • Hourly: ${state.costs['hourly']:.2f}")
        print(f"  • Daily: ${state.costs['daily']:.2f}")
        print(f"  • Monthly: ${state.costs['monthly']:,.2f}")

    # Find optimization opportunities
    print("\n🎯 Finding optimization opportunities...")
    optimization = await ada.find_optimization(state)

    if optimization:
        print(f"  Found: {optimization['type'].value} optimization")
        plan = await ada.create_plan(optimization)

        print(f"\n📋 Optimization Plan:")
        print(f"  • Type: {plan.optimization_type.value}")
        print(f"  • Target: {plan.target}")
        print(f"  • Action: {plan.action}")
        print(f"  • Reason: {plan.reason}")
        print(f"  • Risk Score: {plan.risk_score:.2f}")
        print(f"  • Potential Savings: ${plan.estimated_savings:.2f}/hour")

        if plan.risk_score < 0.3:
            print(f"\n✅ Risk score below threshold - can auto-execute")
            print(f"  (In production, this would execute automatically)")

            # Simulate execution and learn from outcome
            print(f"\n📝 Recording optimization in memory...")
            await memory.remember(
                f"ada-optimize: {plan.optimization_type.value}",
                f"Target: {plan.target}, Action: {plan.action}",
                None,
                {
                    "type": plan.optimization_type.value,
                    "target": plan.target,
                    "risk": plan.risk_score,
                    "savings": plan.estimated_savings
                },
                2.0
            )
        else:
            print(f"\n⚠️ Risk score too high - requires manual approval")
    else:
        print("  ✅ No optimizations needed - system is optimal!")

    # Get ADA status
    status = await ada.get_status()
    print(f"\n📈 ADA Status:")
    print(f"  • Total optimizations: {status['total_optimizations']}")
    print(f"  • Success rate: {status['success_rate']:.1%}")
    print(f"  • Monthly savings: ${status['monthly_savings']:,.2f}")


async def example_4_full_integration():
    """
    Example 4: Complete integration showing all features working together
    """
    print("\n\n" + "=" * 60)
    print("Example 4: Complete Cognitive System Integration")
    print("=" * 60)

    memory_dir = str(Path.home() / ".aishell" / "memory")
    memory = CognitiveMemory(memory_dir=memory_dir)

    print("\n🧠 Cognitive System Initialized")
    print("  ✓ Memory: Semantic search with pattern recognition")
    print("  ✓ Anomaly Detection: Statistical + pattern-based")
    print("  ✓ Autonomous DevOps: Self-optimizing infrastructure")

    print("\n📚 Learning Cycle:")
    print("  1. System executes commands")
    print("  2. Memory records patterns and outcomes")
    print("  3. Anomaly detector learns normal behavior")
    print("  4. ADA learns from successful optimizations")
    print("  5. Future decisions informed by past experience")

    # Demonstrate the learning loop
    print("\n🔄 Simulating learning loop...")

    # Step 1: Record a database optimization
    print("\n  Step 1: Execute database optimization")
    await memory.remember(
        "ANALYZE TABLE users",
        "Analysis complete, 1.2M rows",
        None,
        {"db": "production", "action": "optimize"},
        5.3
    )
    print("    ✓ Recorded in memory")

    # Step 2: Detect that it improved performance
    print("\n  Step 2: Detect performance improvement")
    collector = MetricCollector()
    detector = AnomalyDetector(memory=memory)
    metrics = await collector.collect()
    anomalies = await detector.detect_anomalies(metrics)
    print(f"    ✓ Anomalies detected: {len(anomalies)}")

    # Step 3: ADA learns that this optimization was successful
    print("\n  Step 3: ADA records successful optimization")
    ada = AutonomousDevOps(memory=memory)
    await memory.remember(
        "ada-optimize: performance",
        "Database analysis improved query speed by 40%",
        None,
        {"type": "performance", "improvement": 0.40, "target": "database"},
        1.0
    )
    print("    ✓ Success pattern recorded")

    # Step 4: Next time, system suggests this optimization proactively
    print("\n  Step 4: System learns to suggest optimization proactively")
    suggestions = await memory.recall_by_pattern("pattern:performance", k=3)
    print(f"    ✓ Found {len(suggestions)} similar patterns")
    for suggestion in suggestions[:2]:
        print(f"      - {suggestion.command}")

    print("\n✨ Result: Self-improving intelligent system!")
    print("  • Learns from experience")
    print("  • Adapts to patterns")
    print("  • Optimizes autonomously")
    print("  • Reduces operational overhead")


async def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("COGNITIVE FEATURES INTEGRATION EXAMPLES")
    print("=" * 60)

    try:
        # Run each example
        await example_1_memory_learning()
        await example_2_anomaly_detection_with_memory()
        await example_3_autonomous_devops_with_learning()
        await example_4_full_integration()

        print("\n\n" + "=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)

        print("\n📖 See also:")
        print("  • docs/howto/COGNITIVE_MEMORY.md")
        print("  • docs/howto/ANOMALY_DETECTION.md")
        print("  • docs/howto/AUTONOMOUS_DEVOPS.md")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
