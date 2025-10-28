#!/usr/bin/env ts-node
/**
 * CLI Wrapper Framework Demo
 * Demonstrates all capabilities of the CLI wrapper
 */

import { CLIWrapper, CLIOptions, CommandResult } from '../src/cli/cli-wrapper';
import chalk from 'chalk';

/**
 * Demo 1: Basic Command Execution
 */
async function demo1BasicExecution() {
  console.log(chalk.cyan.bold('\n=== Demo 1: Basic Command Execution ===\n'));

  const wrapper = new CLIWrapper();

  // Execute a simple health check
  const result = await wrapper.executeCommand('health-check', [], { dryRun: true });

  console.log('Command executed:', result.success ? chalk.green('SUCCESS') : chalk.red('FAILED'));
  console.log('Duration:', `${result.duration}ms`);
  console.log('Request ID:', result.metadata?.requestId);

  return wrapper;
}

/**
 * Demo 2: Output Formatting
 */
async function demo2Formatting(wrapper: CLIWrapper) {
  console.log(chalk.cyan.bold('\n=== Demo 2: Output Formatting ===\n'));

  // JSON format
  console.log(chalk.yellow('1. JSON Format:'));
  await wrapper.executeCommand('health-check', [], {
    format: 'json',
    dryRun: true
  });

  // Table format
  console.log(chalk.yellow('\n2. Table Format:'));
  await wrapper.executeCommand('backup-list', [], {
    format: 'table',
    dryRun: true
  });

  // CSV format
  console.log(chalk.yellow('\n3. CSV Format:'));
  await wrapper.executeCommand('backup-list', [], {
    format: 'csv',
    limit: 3,
    dryRun: true
  });
}

/**
 * Demo 3: Global Flags
 */
async function demo3GlobalFlags(wrapper: CLIWrapper) {
  console.log(chalk.cyan.bold('\n=== Demo 3: Global Flags ===\n'));

  // Verbose mode
  console.log(chalk.yellow('1. Verbose Mode:'));
  await wrapper.executeCommand('health-check', [], {
    verbose: true,
    dryRun: true
  });

  // Explain mode
  console.log(chalk.yellow('\n2. Explain Mode:'));
  await wrapper.executeCommand('backup', [], {
    explain: true,
    dryRun: true
  });

  // Dry-run mode
  console.log(chalk.yellow('\n3. Dry-Run Mode:'));
  await wrapper.executeCommand('backup', [], {
    dryRun: true
  });

  // Timestamps
  console.log(chalk.yellow('\n4. Timestamps:'));
  await wrapper.executeCommand('health-check', [], {
    timestamps: true,
    dryRun: true
  });

  // Limit results
  console.log(chalk.yellow('\n5. Limit Results:'));
  await wrapper.executeCommand('backup-list', [], {
    limit: 5,
    dryRun: true
  });
}

/**
 * Demo 4: Command Aliases
 */
async function demo4Aliases(wrapper: CLIWrapper) {
  console.log(chalk.cyan.bold('\n=== Demo 4: Command Aliases ===\n'));

  // Show all registered commands and their aliases
  const commands = wrapper.getRegisteredCommands();

  console.log(chalk.yellow('Commands with Aliases:\n'));

  commands.forEach(cmd => {
    if (cmd.aliases.length > 0) {
      console.log(chalk.green(`  ${cmd.name.padEnd(25)}`), chalk.dim(`→ ${cmd.aliases.join(', ')}`));
    }
  });

  console.log(chalk.yellow('\n\nUsing Aliases:'));

  // Use optimize alias
  console.log(chalk.cyan('\n1. optimize → opt'));
  await wrapper.executeCommand('opt', ['SELECT * FROM users'], { dryRun: true });

  // Use health-check alias
  console.log(chalk.cyan('\n2. health-check → health'));
  await wrapper.executeCommand('health', [], { dryRun: true });

  // Use backup-list alias
  console.log(chalk.cyan('\n3. backup-list → backups'));
  await wrapper.executeCommand('backups', [], { dryRun: true });
}

/**
 * Demo 5: Environment Variables
 */
async function demo5Environment(wrapper: CLIWrapper) {
  console.log(chalk.cyan.bold('\n=== Demo 5: Environment Variables ===\n'));

  console.log(chalk.yellow('Environment Variables:'));
  console.log(`  DATABASE_URL: ${process.env.DATABASE_URL || chalk.red('NOT SET')}`);
  console.log(`  ANTHROPIC_API_KEY: ${process.env.ANTHROPIC_API_KEY ? chalk.green('SET') : chalk.red('NOT SET')}`);
  console.log(`  REDIS_URL: ${process.env.REDIS_URL || chalk.yellow('NOT SET (optional)')}`);

  // Set test environment variables
  process.env.DATABASE_URL = 'postgresql://localhost:5432/test';
  process.env.REDIS_URL = 'redis://localhost:6379';

  console.log(chalk.yellow('\n\nCommands using environment variables:'));

  // Health check uses DATABASE_URL
  console.log(chalk.cyan('\n1. Health Check (uses DATABASE_URL):'));
  await wrapper.executeCommand('health-check', [], { dryRun: true });

  // Cache enable uses REDIS_URL
  console.log(chalk.cyan('\n2. Cache Enable (uses REDIS_URL):'));
  await wrapper.executeCommand('cache-enable', [], { dryRun: true });
}

/**
 * Demo 6: Error Handling
 */
async function demo6ErrorHandling(wrapper: CLIWrapper) {
  console.log(chalk.cyan.bold('\n=== Demo 6: Error Handling ===\n'));

  // Unknown command
  console.log(chalk.yellow('1. Unknown Command:'));
  let result = await wrapper.executeCommand('unknown-command', [], {});
  console.log('Result:', result.success ? 'Success' : chalk.red('Failed (expected)'));
  console.log('Error:', result.error);

  // Missing required arguments
  console.log(chalk.yellow('\n2. Missing Arguments:'));
  result = await wrapper.executeCommand('optimize', [], {});
  console.log('Result:', result.success ? 'Success' : chalk.red('Failed (expected)'));
  console.log('Error:', result.error);

  // Invalid file
  console.log(chalk.yellow('\n3. Invalid File:'));
  result = await wrapper.executeCommand('validate-schema', ['nonexistent.json'], {});
  console.log('Result:', result.success ? 'Success' : chalk.red('Failed (expected)'));
  console.log('Error:', result.error instanceof Error ? result.error.message : result.error);
}

/**
 * Demo 7: File Output
 */
async function demo7FileOutput(wrapper: CLIWrapper) {
  console.log(chalk.cyan.bold('\n=== Demo 7: File Output ===\n'));

  const fs = await import('fs/promises');
  const outputDir = '/tmp/cli-wrapper-demo';

  // Create output directory
  await fs.mkdir(outputDir, { recursive: true });

  // JSON output
  console.log(chalk.yellow('1. JSON Output:'));
  const jsonFile = `${outputDir}/health-check.json`;
  await wrapper.executeCommand('health-check', [], {
    format: 'json',
    output: jsonFile,
    dryRun: true
  });
  console.log(chalk.green(`  Saved to: ${jsonFile}`));

  // CSV output
  console.log(chalk.yellow('\n2. CSV Output:'));
  const csvFile = `${outputDir}/backups.csv`;
  await wrapper.executeCommand('backup-list', [], {
    format: 'csv',
    output: csvFile,
    dryRun: true
  });
  console.log(chalk.green(`  Saved to: ${csvFile}`));

  // Table output to file
  console.log(chalk.yellow('\n3. Table Output to File:'));
  const tableFile = `${outputDir}/cache-stats.txt`;
  await wrapper.executeCommand('cache-stats', [], {
    format: 'table',
    output: tableFile,
    dryRun: true
  });
  console.log(chalk.green(`  Saved to: ${tableFile}`));

  console.log(chalk.cyan('\n\nGenerated files:'));
  const files = await fs.readdir(outputDir);
  files.forEach(file => console.log(chalk.dim(`  - ${outputDir}/${file}`)));
}

/**
 * Demo 8: Advanced Options
 */
async function demo8AdvancedOptions(wrapper: CLIWrapper) {
  console.log(chalk.cyan.bold('\n=== Demo 8: Advanced Options ===\n'));

  // Multiple flags combined
  console.log(chalk.yellow('1. Multiple Flags Combined:'));
  await wrapper.executeCommand('optimize', ['SELECT * FROM users WHERE id > 100'], {
    format: 'json',
    verbose: true,
    explain: true,
    timestamps: true,
    dryRun: true
  });

  // Timeout handling
  console.log(chalk.yellow('\n2. Timeout Configuration:'));
  await wrapper.executeCommand('health-check', [], {
    timeout: 10000, // 10 seconds
    verbose: true,
    dryRun: true
  });

  // Database override
  console.log(chalk.yellow('\n3. Database Override:'));
  await wrapper.executeCommand('backup', [], {
    database: 'custom-database',
    explain: true,
    dryRun: true
  });
}

/**
 * Demo 9: Command Categories
 */
async function demo9Categories(wrapper: CLIWrapper) {
  console.log(chalk.cyan.bold('\n=== Demo 9: Command Categories ===\n'));

  const commands = wrapper.getRegisteredCommands();

  // Group by category
  const categories: Record<string, typeof commands> = {
    'Query Optimization': [],
    'Health & Monitoring': [],
    'Backup & Recovery': [],
    'Cache Management': [],
    'Schema Management': [],
    'SQL Tools': [],
    'Cost Optimization': [],
    'Other': []
  };

  commands.forEach(cmd => {
    if (['optimize', 'analyze-slow-queries'].includes(cmd.name)) {
      categories['Query Optimization'].push(cmd);
    } else if (['health-check', 'monitor'].includes(cmd.name)) {
      categories['Health & Monitoring'].push(cmd);
    } else if (['backup', 'restore', 'backup-list'].includes(cmd.name)) {
      categories['Backup & Recovery'].push(cmd);
    } else if (cmd.name.startsWith('cache-')) {
      categories['Cache Management'].push(cmd);
    } else if (['design-schema', 'validate-schema', 'diff'].includes(cmd.name)) {
      categories['Schema Management'].push(cmd);
    } else if (['explain', 'translate'].includes(cmd.name)) {
      categories['SQL Tools'].push(cmd);
    } else if (cmd.name.includes('cost')) {
      categories['Cost Optimization'].push(cmd);
    } else {
      categories['Other'].push(cmd);
    }
  });

  // Display categories
  Object.entries(categories).forEach(([category, cmds]) => {
    if (cmds.length > 0) {
      console.log(chalk.bold.yellow(`\n${category}:`));
      cmds.forEach(cmd => {
        console.log(chalk.green(`  • ${cmd.name.padEnd(25)}`), chalk.dim(cmd.description));
      });
    }
  });

  console.log(chalk.cyan(`\n\nTotal Commands: ${commands.length}`));
}

/**
 * Demo 10: Programmatic Usage
 */
async function demo10Programmatic(wrapper: CLIWrapper) {
  console.log(chalk.cyan.bold('\n=== Demo 10: Programmatic Usage ===\n'));

  console.log(chalk.yellow('Executing multiple commands programmatically:\n'));

  // Execute multiple commands in sequence
  const commands = [
    { name: 'health-check', args: [], options: { format: 'json' as const } },
    { name: 'backup-list', args: [], options: { format: 'table' as const, limit: 3 } },
    { name: 'cache-stats', args: [], options: { format: 'csv' as const } }
  ];

  for (const cmd of commands) {
    console.log(chalk.cyan(`Executing: ${cmd.name}`));
    const result = await wrapper.executeCommand(cmd.name, cmd.args, {
      ...cmd.options,
      dryRun: true
    });

    console.log(
      `  Status: ${result.success ? chalk.green('✓') : chalk.red('✗')} ` +
      `Duration: ${result.duration}ms`
    );
  }

  // Parallel execution (be careful with rate limits)
  console.log(chalk.yellow('\n\nParallel execution:\n'));

  const results = await Promise.all([
    wrapper.executeCommand('health-check', [], { dryRun: true }),
    wrapper.executeCommand('cache-stats', [], { dryRun: true }),
    wrapper.executeCommand('backup-list', [], { limit: 1, dryRun: true })
  ]);

  results.forEach((result, i) => {
    console.log(
      `  Command ${i + 1}: ${result.success ? chalk.green('✓') : chalk.red('✗')} ` +
      `(${result.duration}ms)`
    );
  });
}

/**
 * Main demo runner
 */
async function main() {
  console.log(chalk.cyan.bold('\n╔════════════════════════════════════════════╗'));
  console.log(chalk.cyan.bold('║   CLI Wrapper Framework - Full Demo       ║'));
  console.log(chalk.cyan.bold('╚════════════════════════════════════════════╝\n'));

  try {
    // Set required environment variables
    process.env.ANTHROPIC_API_KEY = process.env.ANTHROPIC_API_KEY || 'demo-api-key';

    const wrapper = await demo1BasicExecution();
    await demo2Formatting(wrapper);
    await demo3GlobalFlags(wrapper);
    await demo4Aliases(wrapper);
    await demo5Environment(wrapper);
    await demo6ErrorHandling(wrapper);
    await demo7FileOutput(wrapper);
    await demo8AdvancedOptions(wrapper);
    await demo9Categories(wrapper);
    await demo10Programmatic(wrapper);

    // Cleanup
    console.log(chalk.cyan.bold('\n\n=== Cleanup ===\n'));
    await wrapper.cleanup();
    console.log(chalk.green('✓ Cleanup complete'));

    console.log(chalk.cyan.bold('\n\n╔════════════════════════════════════════════╗'));
    console.log(chalk.cyan.bold('║   Demo completed successfully!             ║'));
    console.log(chalk.cyan.bold('╚════════════════════════════════════════════╝\n'));

  } catch (error) {
    console.error(chalk.red('\n\nDemo failed:'), error);
    process.exit(1);
  }
}

// Run demo if executed directly
if (require.main === module) {
  main();
}

export { main };
