"""
Cognitive features command handlers for argparse-based CLI.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from ..cognitive.memory import CognitiveMemory
from ..cognitive.anomaly_detector import AnomalyDetector, MetricCollector
from ..cognitive.autonomous_devops import AutonomousDevOps

console = Console()


async def handle_memory_command(args):
    """Handle memory subcommands."""
    memory_dir = str(Path.home() / ".aishell" / "memory")
    memory = CognitiveMemory(memory_dir=memory_dir)

    if args.memory_command == 'recall':
        await handle_memory_recall(memory, args)
    elif args.memory_command == 'insights':
        await handle_memory_insights(memory, args)
    elif args.memory_command == 'suggest':
        await handle_memory_suggest(memory, args)
    elif args.memory_command == 'export':
        await handle_memory_export(memory, args)
    elif args.memory_command == 'import':
        await handle_memory_import(memory, args)
    else:
        console.print("[red]Unknown memory command. Use --help for options.[/red]")
        sys.exit(1)


async def handle_memory_recall(memory: CognitiveMemory, args):
    """Recall similar commands."""
    memories = await memory.recall(args.query, k=args.limit, threshold=args.threshold)

    if not memories:
        console.print(f"[yellow]No memories found matching '{args.query}'[/yellow]")
        return

    table = Table(title=f"Memories matching: {args.query}", box=box.ROUNDED)
    table.add_column("Command", style="cyan", no_wrap=False)
    table.add_column("Success", justify="center", style="green")
    table.add_column("Import", justify="right", style="magenta")
    table.add_column("Freq", justify="right", style="blue")

    for mem in memories:
        success_icon = "✓" if mem.success else "✗"
        success_style = "green" if mem.success else "red"
        table.add_row(
            mem.command[:60] + "..." if len(mem.command) > 60 else mem.command,
            f"[{success_style}]{success_icon}[/{success_style}]",
            f"{mem.importance:.2f}",
            str(mem.frequency)
        )

    console.print(table)


async def handle_memory_insights(memory: CognitiveMemory, args):
    """Show memory insights."""
    insights = await memory.get_insights()

    if args.json_output:
        console.print_json(data=insights)
        return

    # Most used commands
    if insights['most_used_commands']:
        table = Table(title="Most Used Commands", box=box.ROUNDED)
        table.add_column("Command", style="cyan")
        table.add_column("Usage Count", justify="right", style="blue")

        for cmd in insights['most_used_commands'][:10]:
            table.add_row(cmd['command'], str(cmd['count']))

        console.print(table)

    # Overall statistics
    stats_panel = Panel(
        f"""[bold cyan]Overall Statistics:[/bold cyan]
  • Success Rate: {insights['overall_success_rate']:.1%}
  • Total Memories: {insights['total_memories']:,}
  • Avg Importance: {insights['avg_importance']:.2f}
  • Avg Sentiment: {insights['avg_sentiment']:.2f}""",
        title="Memory Stats",
        border_style="green"
    )
    console.print(stats_panel)

    # Common errors
    if insights['common_errors']:
        error_table = Table(title="Common Errors", box=box.ROUNDED)
        error_table.add_column("Error", style="red")
        error_table.add_column("Count", justify="right")

        for error in insights['common_errors'][:5]:
            error_table.add_row(error['error'][:50], str(error['count']))

        console.print(error_table)


async def handle_memory_suggest(memory: CognitiveMemory, args):
    """Get command suggestions."""
    context = {}
    if args.context:
        try:
            context = json.loads(args.context)
        except json.JSONDecodeError:
            console.print("[red]Invalid JSON context[/red]")
            sys.exit(1)

    suggestions = await memory.get_command_suggestions(context, k=3)

    if not suggestions:
        console.print("[yellow]No suggestions available[/yellow]")
        return

    console.print("[bold cyan]Command Suggestions:[/bold cyan]")
    for i, (cmd, confidence) in enumerate(suggestions, 1):
        console.print(f"  {i}. {cmd} (confidence: {confidence:.0%})")


async def handle_memory_export(memory: CognitiveMemory, args):
    """Export knowledge base."""
    try:
        await memory.export_knowledge(args.output_file)
        console.print(f"[green]✓ Knowledge exported to {args.output_file}[/green]")
    except Exception as e:
        console.print(f"[red]✗ Export failed: {e}[/red]")
        sys.exit(1)


async def handle_memory_import(memory: CognitiveMemory, args):
    """Import knowledge base."""
    try:
        await memory.import_knowledge(args.input_file)
        console.print(f"[green]✓ Knowledge imported from {args.input_file}[/green]")
    except Exception as e:
        console.print(f"[red]✗ Import failed: {e}[/red]")
        sys.exit(1)


async def handle_anomaly_command(args):
    """Handle anomaly detection subcommands."""
    if args.anomaly_command == 'start':
        await handle_anomaly_start(args)
    elif args.anomaly_command == 'status':
        await handle_anomaly_status(args)
    elif args.anomaly_command == 'check':
        await handle_anomaly_check(args)
    else:
        console.print("[red]Unknown anomaly command. Use --help for options.[/red]")
        sys.exit(1)


async def handle_anomaly_start(args):
    """Start anomaly monitoring."""
    memory_dir = str(Path.home() / ".aishell" / "memory")
    memory = CognitiveMemory(memory_dir=memory_dir)

    collector = MetricCollector()
    detector = AnomalyDetector(
        memory=memory,
        auto_fix_enabled=not args.no_auto_fix
    )

    console.print(Panel(
        f"""[bold cyan]Anomaly Detection Started[/bold cyan]
  • Check Interval: {args.interval}s
  • Auto-Fix: {'Enabled' if not args.no_auto_fix else 'Disabled'}
  • Press Ctrl+C to stop""",
        title="Status",
        border_style="green"
    ))

    try:
        while True:
            metrics = await collector.collect()
            anomalies = await detector.detect_anomalies(metrics)

            if anomalies:
                console.print(f"\n[yellow]⚠ {len(anomalies)} anomalies detected[/yellow]")
                for anomaly in anomalies:
                    console.print(f"  • {anomaly.type.value}: {anomaly.description}")

                    if not args.no_auto_fix:
                        success = await detector.attempt_auto_remediation(anomaly)
                        if success:
                            console.print(f"    [green]✓ Auto-fixed[/green]")
                        else:
                            console.print(f"    [red]✗ Auto-fix failed[/red]")

            await asyncio.sleep(args.interval)

    except KeyboardInterrupt:
        console.print("\n[yellow]Monitoring stopped[/yellow]")


async def handle_anomaly_status(args):
    """Show anomaly detector status."""
    memory_dir = str(Path.home() / ".aishell" / "memory")
    memory = CognitiveMemory(memory_dir=memory_dir)
    detector = AnomalyDetector(memory=memory)

    status = await detector.get_status()

    if args.json_output:
        console.print_json(data=status)
        return

    # Status panel
    console.print(Panel(
        f"""[bold cyan]Anomaly Detector Status:[/bold cyan]
  • Active Anomalies: {status['active_anomalies']}
  • Total Detected: {status['total_detected']}
  • Auto-Fixes Applied: {status['auto_fixes_applied']}
  • Fixes Remaining This Hour: {status['fixes_remaining_this_hour']}/10""",
        title="Status",
        border_style="green"
    ))

    # Recent anomalies
    if status.get('recent_anomalies'):
        table = Table(title="Recent Anomalies", box=box.ROUNDED)
        table.add_column("Type", style="yellow")
        table.add_column("Severity", style="red")
        table.add_column("Description", style="cyan")

        for anomaly in status['recent_anomalies'][:10]:
            table.add_row(
                anomaly['type'],
                anomaly['severity'],
                anomaly['description'][:50]
            )

        console.print(table)


async def handle_anomaly_check(args):
    """Run immediate anomaly check."""
    memory_dir = str(Path.home() / ".aishell" / "memory")
    memory = CognitiveMemory(memory_dir=memory_dir)

    collector = MetricCollector()
    detector = AnomalyDetector(memory=memory)

    console.print("[cyan]Running anomaly check...[/cyan]")

    metrics = await collector.collect()
    anomalies = await detector.detect_anomalies(metrics)

    if not anomalies:
        console.print("[green]✓ No anomalies detected[/green]")
        return

    console.print(f"\n[yellow]Found {len(anomalies)} anomalies:[/yellow]")

    table = Table(box=box.ROUNDED)
    table.add_column("Type", style="yellow")
    table.add_column("Severity", style="red")
    table.add_column("Description", style="cyan")

    for anomaly in anomalies:
        table.add_row(
            anomaly.type.value,
            anomaly.severity.value,
            anomaly.description
        )

    console.print(table)


async def handle_ada_command(args):
    """Handle ADA (Autonomous DevOps Agent) subcommands."""
    if args.ada_command == 'start':
        await handle_ada_start(args)
    elif args.ada_command == 'status':
        await handle_ada_status(args)
    elif args.ada_command == 'analyze':
        await handle_ada_analyze(args)
    elif args.ada_command == 'optimize':
        await handle_ada_optimize(args)
    else:
        console.print("[red]Unknown ADA command. Use --help for options.[/red]")
        sys.exit(1)


async def handle_ada_start(args):
    """Start Autonomous DevOps Agent."""
    memory_dir = str(Path.home() / ".aishell" / "memory")
    memory = CognitiveMemory(memory_dir=memory_dir)
    ada = AutonomousDevOps(memory=memory)

    console.print(Panel(
        f"""[bold cyan]Autonomous DevOps Agent Started[/bold cyan]
  • Optimization Interval: {args.interval}s
  • Features: Auto-optimize, Auto-scale, Auto-heal
  • Press Ctrl+C to stop""",
        title="ADA",
        border_style="green"
    ))

    try:
        while True:
            # Analyze infrastructure
            state = await ada.analyze_infrastructure()

            # Find optimization opportunities
            optimization = await ada.find_optimization(state)

            if optimization:
                console.print(f"\n[cyan]Found optimization: {optimization['type'].value}[/cyan]")

                # Create and execute plan
                plan = await ada.create_plan(optimization)
                console.print(f"  • Target: {plan.target}")
                console.print(f"  • Risk: {plan.risk_score:.2f}")

                if plan.risk_score < 0.3:
                    console.print("  [green]→ Auto-executing (low risk)...[/green]")
                    success = await ada.execute_plan(plan)
                    if success:
                        console.print("  [green]✓ Optimization successful[/green]")
                    else:
                        console.print("  [red]✗ Optimization failed[/red]")
                else:
                    console.print(f"  [yellow]⚠ Manual approval required (risk: {plan.risk_score:.2f})[/yellow]")

            await asyncio.sleep(args.interval)

    except KeyboardInterrupt:
        console.print("\n[yellow]ADA stopped[/yellow]")


async def handle_ada_status(args):
    """Show ADA status."""
    memory_dir = str(Path.home() / ".aishell" / "memory")
    memory = CognitiveMemory(memory_dir=memory_dir)
    ada = AutonomousDevOps(memory=memory)

    status = await ada.get_status()

    if args.json_output:
        console.print_json(data=status)
        return

    # Status panel
    console.print(Panel(
        f"""[bold cyan]ADA Status:[/bold cyan]
  • Active Plans: {status['active_plans']}
  • Total Optimizations: {status['total_optimizations']}
  • Success Rate: {status['success_rate']:.1%}
  • Monthly Savings: ${status['monthly_savings']:,.2f}""",
        title="Status",
        border_style="green"
    ))

    # Success rates by type
    if status.get('success_by_type'):
        table = Table(title="Success Rates by Type", box=box.ROUNDED)
        table.add_column("Type", style="cyan")
        table.add_column("Success Rate", justify="right", style="green")

        for opt_type, rate in status['success_by_type'].items():
            table.add_row(opt_type, f"{rate:.1%}")

        console.print(table)


async def handle_ada_analyze(args):
    """Analyze infrastructure."""
    memory_dir = str(Path.home() / ".aishell" / "memory")
    memory = CognitiveMemory(memory_dir=memory_dir)
    ada = AutonomousDevOps(memory=memory)

    console.print("[cyan]Analyzing infrastructure...[/cyan]")

    state = await ada.analyze_infrastructure()

    # Services table
    if state.services:
        table = Table(title="Services", box=box.ROUNDED)
        table.add_column("Service", style="cyan")
        table.add_column("Version", style="blue")
        table.add_column("Inst", justify="right")
        table.add_column("CPU%", justify="right", style="yellow")
        table.add_column("Memory%", justify="right", style="magenta")
        table.add_column("Health", justify="right", style="green")

        for service in state.services[:10]:
            table.add_row(
                service['name'],
                service['version'],
                str(service['instances']),
                f"{service['cpu_usage']:.1f}",
                f"{service['memory_usage']:.1f}",
                f"{service['health']:.2f}"
            )

        console.print(table)

    # Costs
    if state.costs:
        console.print(Panel(
            f"""[bold cyan]Cost Tracking:[/bold cyan]
  • Hourly: ${state.costs['hourly']:.2f}
  • Daily: ${state.costs['daily']:.2f}
  • Monthly: ${state.costs['monthly']:,.2f}""",
            title="Costs",
            border_style="yellow"
        ))


async def handle_ada_optimize(args):
    """Find and apply optimizations."""
    memory_dir = str(Path.home() / ".aishell" / "memory")
    memory = CognitiveMemory(memory_dir=memory_dir)
    ada = AutonomousDevOps(memory=memory)

    console.print("[cyan]Finding optimizations...[/cyan]")

    # Analyze infrastructure
    state = await ada.analyze_infrastructure()

    # Find optimization
    optimization = await ada.find_optimization(state, optimization_type=args.type)

    if not optimization:
        console.print("[green]No optimizations needed[/green]")
        return

    # Create plan
    plan = await ada.create_plan(optimization)

    # Display plan
    console.print(Panel(
        f"""[bold cyan]Found Optimization:[/bold cyan]
  • Type: {plan.optimization_type.value}
  • Target: {plan.target}
  • Action: {plan.action}
  • Reason: {plan.reason}
  • Risk Score: {plan.risk_score:.2f}
  • Potential Savings: ${plan.estimated_savings:.2f}/hour""",
        title="Optimization Plan",
        border_style="yellow"
    ))

    if args.dry_run:
        console.print("\n[yellow]Dry-run mode: No changes made[/yellow]")
        return

    # Execute plan
    console.print("\n[cyan]Executing plan...[/cyan]")
    success = await ada.execute_plan(plan)

    if success:
        console.print("[green]✓ Optimization completed successfully[/green]")
        if plan.estimated_savings > 0:
            monthly_savings = plan.estimated_savings * 24 * 30
            console.print(f"[green]Monthly savings: ~${monthly_savings:,.2f}[/green]")
    else:
        console.print("[red]✗ Optimization failed[/red]")
        sys.exit(1)
