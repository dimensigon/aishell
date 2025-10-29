/**
 * Monitoring Commands Export
 * Central export for all monitoring CLI commands
 *
 * @module monitoring-commands
 */

import { Command } from 'commander';
import { createMonitoringCommands } from './monitoring-cli';

/**
 * Create and configure monitoring command structure
 */
export function createCommands(): Command {
  const program = new Command();

  program
    .name('ai-shell-monitoring')
    .description('AI-Shell Monitoring & Analytics CLI')
    .version('1.0.0');

  // Add all monitoring commands
  const monitoringCommands = createMonitoringCommands();

  // Transfer commands to main program
  monitoringCommands.commands.forEach((cmd) => {
    program.addCommand(cmd);
  });

  return program;
}

/**
 * Command definitions for external reference
 */
export const commandDefinitions = [
  {
    name: 'health',
    description: 'Perform database health check',
    usage: 'ai-shell health [database]',
    examples: [
      'ai-shell health',
      'ai-shell health postgres-prod',
      'ai-shell health main-db'
    ]
  },
  {
    name: 'monitor start',
    description: 'Start real-time monitoring',
    usage: 'ai-shell monitor start [options]',
    examples: [
      'ai-shell monitor start',
      'ai-shell monitor start --interval 10',
      'ai-shell monitor start --output json',
      'ai-shell monitor start --metrics cpu,memory'
    ]
  },
  {
    name: 'monitor stop',
    description: 'Stop monitoring',
    usage: 'ai-shell monitor stop',
    examples: [
      'ai-shell monitor stop'
    ]
  },
  {
    name: 'metrics show',
    description: 'Show current metrics',
    usage: 'ai-shell metrics show [metric]',
    examples: [
      'ai-shell metrics show',
      'ai-shell metrics show cpuUsage',
      'ai-shell metrics show memoryUsage'
    ]
  },
  {
    name: 'metrics export',
    description: 'Export metrics in various formats',
    usage: 'ai-shell metrics export <format> [options]',
    examples: [
      'ai-shell metrics export json',
      'ai-shell metrics export csv --output metrics.csv',
      'ai-shell metrics export prometheus',
      'ai-shell metrics export grafana --output grafana-data.json'
    ]
  },
  {
    name: 'alerts setup',
    description: 'Configure alert settings',
    usage: 'ai-shell alerts setup',
    examples: [
      'ai-shell alerts setup'
    ]
  },
  {
    name: 'alerts list',
    description: 'List active alerts',
    usage: 'ai-shell alerts list',
    examples: [
      'ai-shell alerts list'
    ]
  },
  {
    name: 'alerts test',
    description: 'Test alert notification',
    usage: 'ai-shell alerts test <alert-id>',
    examples: [
      'ai-shell alerts test responseTime-1234567890',
      'ai-shell alerts test cpu-alert'
    ]
  },
  {
    name: 'performance analyze',
    description: 'Analyze system performance',
    usage: 'ai-shell performance analyze',
    examples: [
      'ai-shell performance analyze'
    ]
  },
  {
    name: 'performance report',
    description: 'Generate performance report',
    usage: 'ai-shell performance report [period]',
    examples: [
      'ai-shell performance report',
      'ai-shell performance report 1h',
      'ai-shell performance report 24h',
      'ai-shell performance report 7d'
    ]
  },
  {
    name: 'dashboard',
    description: 'Start monitoring dashboard',
    usage: 'ai-shell dashboard [options]',
    examples: [
      'ai-shell dashboard',
      'ai-shell dashboard --port 3000',
      'ai-shell dashboard --host localhost --port 8080'
    ]
  },
  {
    name: 'grafana setup',
    description: 'Configure Grafana connection',
    usage: 'ai-shell grafana setup --url <url> --api-key <key> [options]',
    examples: [
      'ai-shell grafana setup --url http://localhost:3000 --api-key your-api-key',
      'ai-shell grafana setup --url http://grafana.example.com --api-key key --prometheus-url http://localhost:9090'
    ]
  },
  {
    name: 'grafana deploy-dashboards',
    description: 'Deploy all dashboards to Grafana',
    usage: 'ai-shell grafana deploy-dashboards',
    examples: [
      'ai-shell grafana deploy-dashboards'
    ]
  },
  {
    name: 'prometheus',
    description: 'Configure Prometheus integration',
    usage: 'ai-shell prometheus [options]',
    examples: [
      'ai-shell prometheus',
      'ai-shell prometheus --port 9090',
      'ai-shell prometheus --host 0.0.0.0 --port 9091'
    ]
  },
  {
    name: 'anomaly',
    description: 'Detect anomalies in metrics',
    usage: 'ai-shell anomaly [options]',
    examples: [
      'ai-shell anomaly',
      'ai-shell anomaly --metric cpuUsage',
      'ai-shell anomaly --threshold 3 --window 60',
      'ai-shell anomaly --sensitivity high --window 120'
    ]
  }
];

/**
 * Get command by name
 */
export function getCommandDefinition(name: string) {
  return commandDefinitions.find(cmd => cmd.name === name);
}

/**
 * List all commands
 */
export function listCommands(): string[] {
  return commandDefinitions.map(cmd => cmd.name);
}

/**
 * Get command help text
 */
export function getCommandHelp(name: string): string {
  const def = getCommandDefinition(name);
  if (!def) {
    return `Command '${name}' not found`;
  }

  return `
Command: ${def.name}
Description: ${def.description}
Usage: ${def.usage}

Examples:
${def.examples.map(ex => `  ${ex}`).join('\n')}
  `.trim();
}
