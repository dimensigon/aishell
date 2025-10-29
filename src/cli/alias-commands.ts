import { Command } from 'commander';
import { AliasManager } from './alias-manager';
import { createLogger } from '../core/logger';
import * as chalk from 'chalk';

const logger = createLogger('AliasCLI');

export function registerAliasCommands(program: Command): void {
  const aliasManager = new AliasManager();

  const alias = program
    .command('alias')
    .description('Manage query aliases for shortcuts and parameterized queries');

  // alias add
  alias
    .command('add <name> <query>')
    .description('Add a new query alias')
    .option('-d, --description <text>', 'Alias description')
    .option('-p, --parameters <list>', 'Parameterized alias (format: name:type:required:default,...)')
    .option('-t, --tags <tags>', 'Comma-separated tags')
    .action(async (name: string, query: string, options: {
      description?: string;
      parameters?: string;
      tags?: string;
    }) => {
      try {
        await aliasManager.initialize();

        const tags = options.tags ? options.tags.split(',').map(t => t.trim()) : undefined;

        await aliasManager.addAlias(name, query, {
          description: options.description,
          parameters: options.parameters,
          tags
        });

        console.log(chalk.green(`✓ Alias '${name}' added successfully`));

        if (options.parameters) {
          console.log(chalk.gray('\nParameters:'));
          const params = options.parameters.split(',');
          params.forEach((p, i) => {
            console.log(chalk.gray(`  $${i + 1}: ${p}`));
          });
        }

        console.log(chalk.gray(`\nRun with: ai-shell alias run ${name} [args...]`));
      } catch (error) {
        console.error(chalk.red(`Error: ${(error as Error).message}`));
        process.exit(1);
      }
    });

  // alias remove
  alias
    .command('remove <name>')
    .alias('rm')
    .description('Remove an alias')
    .action(async (name: string) => {
      try {
        await aliasManager.initialize();
        await aliasManager.removeAlias(name);
        console.log(chalk.green(`✓ Alias '${name}' removed successfully`));
      } catch (error) {
        console.error(chalk.red(`Error: ${(error as Error).message}`));
        process.exit(1);
      }
    });

  // alias list
  alias
    .command('list')
    .alias('ls')
    .description('List all aliases')
    .option('-v, --verbose', 'Show full queries and details')
    .option('-f, --format <type>', 'Output format (table, json, yaml)', 'table')
    .option('-t, --tags <tags>', 'Filter by tags (comma-separated)')
    .action(async (options: {
      verbose?: boolean;
      format: 'table' | 'json' | 'yaml';
      tags?: string;
    }) => {
      try {
        await aliasManager.initialize();

        const tags = options.tags ? options.tags.split(',').map(t => t.trim()) : undefined;

        const aliases = await aliasManager.listAliases({
          verbose: options.verbose,
          format: options.format,
          tags
        });

        if (aliases.length === 0) {
          console.log(chalk.yellow('No aliases found'));
          return;
        }

        if (options.format === 'json') {
          console.log(JSON.stringify(aliases, null, 2));
        } else if (options.format === 'yaml') {
          const yaml = await import('js-yaml');
          console.log(yaml.dump(aliases, { indent: 2 }));
        } else {
          // Table format
          console.log(chalk.bold('\nAliases:'));
          console.log(chalk.gray('─'.repeat(80)));

          aliases.forEach(alias => {
            console.log(chalk.cyan(`\n${alias.name}`) + chalk.gray(` (used ${alias.usageCount} times)`));

            if (alias.description) {
              console.log(chalk.gray(`  ${alias.description}`));
            }

            if (options.verbose) {
              console.log(chalk.white(`  Query: ${alias.query}`));
            }

            if (alias.parameters && alias.parameters.length > 0) {
              console.log(chalk.gray('  Parameters:'));
              alias.parameters.forEach((p, i) => {
                const req = p.required ? 'required' : 'optional';
                const def = p.default !== undefined ? ` = ${p.default}` : '';
                console.log(chalk.gray(`    $${i + 1}: ${p.name} (${p.type}, ${req}${def})`));
              });
            }

            if (alias.tags && alias.tags.length > 0) {
              console.log(chalk.gray(`  Tags: ${alias.tags.join(', ')}`));
            }

            if (alias.lastUsed) {
              console.log(chalk.gray(`  Last used: ${alias.lastUsed.toLocaleString()}`));
            }
          });

          console.log(chalk.gray('\n' + '─'.repeat(80)));
          console.log(chalk.gray(`Total: ${aliases.length} aliases\n`));
        }
      } catch (error) {
        console.error(chalk.red(`Error: ${(error as Error).message}`));
        process.exit(1);
      }
    });

  // alias show
  alias
    .command('show <name>')
    .description('Show details for a specific alias')
    .action(async (name: string) => {
      try {
        await aliasManager.initialize();

        const alias = await aliasManager.showAlias(name);
        if (!alias) {
          console.log(chalk.yellow(`Alias '${name}' not found`));
          return;
        }

        console.log(chalk.bold(`\n${alias.name}`));
        console.log(chalk.gray('─'.repeat(80)));

        if (alias.description) {
          console.log(chalk.white(`Description: ${alias.description}`));
        }

        console.log(chalk.white(`Query: ${alias.query}`));

        if (alias.parameters && alias.parameters.length > 0) {
          console.log(chalk.white('\nParameters:'));
          alias.parameters.forEach((p, i) => {
            const req = p.required ? chalk.red('required') : chalk.gray('optional');
            const def = p.default !== undefined ? chalk.gray(` = ${p.default}`) : '';
            console.log(`  $${i + 1}: ${chalk.cyan(p.name)} (${chalk.yellow(p.type)}, ${req}${def})`);
            if (p.description) {
              console.log(chalk.gray(`      ${p.description}`));
            }
          });
        }

        if (alias.tags && alias.tags.length > 0) {
          console.log(chalk.white(`\nTags: ${alias.tags.join(', ')}`));
        }

        console.log(chalk.gray(`\nCreated: ${alias.createdAt.toLocaleString()}`));
        console.log(chalk.gray(`Usage count: ${alias.usageCount}`));

        if (alias.lastUsed) {
          console.log(chalk.gray(`Last used: ${alias.lastUsed.toLocaleString()}`));
        }

        console.log(chalk.gray('\n' + '─'.repeat(80) + '\n'));

        // Show usage example
        console.log(chalk.bold('Usage:'));
        const args = alias.parameters?.map((p, i) => `<${p.name}>`).join(' ') || '';
        console.log(chalk.cyan(`  ai-shell alias run ${name} ${args}`));
        console.log();
      } catch (error) {
        console.error(chalk.red(`Error: ${(error as Error).message}`));
        process.exit(1);
      }
    });

  // alias edit
  alias
    .command('edit <name>')
    .description('Edit an existing alias')
    .option('-q, --query <query>', 'New query')
    .option('-d, --description <text>', 'New description')
    .option('-p, --parameters <list>', 'New parameters')
    .option('-t, --tags <tags>', 'New tags (comma-separated)')
    .action(async (name: string, options: {
      query?: string;
      description?: string;
      parameters?: string;
      tags?: string;
    }) => {
      try {
        await aliasManager.initialize();

        const updates: any = {};

        if (options.query) {
          updates.query = options.query;
        }

        if (options.description !== undefined) {
          updates.description = options.description;
        }

        if (options.parameters) {
          // Parse parameters string
          const aliasManager2 = new AliasManager();
          updates.parameters = (aliasManager2 as any).parseParameters(options.parameters);
        }

        if (options.tags !== undefined) {
          updates.tags = options.tags.split(',').map(t => t.trim());
        }

        await aliasManager.editAlias(name, updates);
        console.log(chalk.green(`✓ Alias '${name}' updated successfully`));
      } catch (error) {
        console.error(chalk.red(`Error: ${(error as Error).message}`));
        process.exit(1);
      }
    });

  // alias rename
  alias
    .command('rename <old-name> <new-name>')
    .alias('mv')
    .description('Rename an alias')
    .action(async (oldName: string, newName: string) => {
      try {
        await aliasManager.initialize();
        await aliasManager.renameAlias(oldName, newName);
        console.log(chalk.green(`✓ Alias renamed from '${oldName}' to '${newName}'`));
      } catch (error) {
        console.error(chalk.red(`Error: ${(error as Error).message}`));
        process.exit(1);
      }
    });

  // alias run
  alias
    .command('run <name> [args...]')
    .description('Execute an alias with arguments')
    .option('-e, --explain', 'Show execution plan')
    .option('-d, --dry-run', 'Test without executing')
    .option('-f, --format <type>', 'Output format (table, json, csv)', 'table')
    .action(async (name: string, args: string[], options: {
      explain?: boolean;
      dryRun?: boolean;
      format: 'table' | 'json' | 'csv';
    }) => {
      try {
        await aliasManager.initialize();

        const result = await aliasManager.runAlias(name, args, {
          explain: options.explain,
          dryRun: options.dryRun,
          format: options.format
        });

        if (options.explain || options.dryRun) {
          console.log(chalk.bold('\nExecution Plan:'));
          console.log(chalk.gray('─'.repeat(80)));
          if (result.explanation) {
            console.log(result.explanation);
          } else {
            console.log(chalk.white(`Query: ${result.query}`));
            if (result.parameters.length > 0) {
              console.log(chalk.white(`Parameters: ${result.parameters.join(', ')}`));
            }
          }
          console.log(chalk.gray('─'.repeat(80) + '\n'));

          if (options.dryRun) {
            console.log(chalk.yellow('(Dry run - query not executed)'));
            return;
          }
        }

        // In a real implementation, this would execute the query
        // For now, just show the generated query
        console.log(chalk.green('✓ Generated query:'));
        console.log(chalk.white(result.query));

        // Note: Actual query execution would be handled by the query-executor
        console.log(chalk.gray('\nNote: Query execution would be handled by query-executor'));
      } catch (error) {
        console.error(chalk.red(`Error: ${(error as Error).message}`));
        process.exit(1);
      }
    });

  // alias export
  alias
    .command('export <file>')
    .description('Export all aliases to a file')
    .option('-f, --format <type>', 'Export format (json, yaml)', 'json')
    .action(async (file: string, options: { format: 'json' | 'yaml' }) => {
      try {
        await aliasManager.initialize();
        await aliasManager.exportAliases(file, options.format);
        console.log(chalk.green(`✓ Aliases exported to ${file}`));
      } catch (error) {
        console.error(chalk.red(`Error: ${(error as Error).message}`));
        process.exit(1);
      }
    });

  // alias import
  alias
    .command('import <file>')
    .description('Import aliases from a file')
    .option('-m, --merge', 'Merge with existing aliases (default: replace)')
    .action(async (file: string, options: { merge?: boolean }) => {
      try {
        await aliasManager.initialize();
        await aliasManager.importAliases(file, options.merge || false);
        console.log(chalk.green(`✓ Aliases imported from ${file}`));
      } catch (error) {
        console.error(chalk.red(`Error: ${(error as Error).message}`));
        process.exit(1);
      }
    });

  // alias template subcommand
  const template = alias
    .command('template')
    .description('Manage alias templates');

  template
    .command('list')
    .description('List all available templates')
    .action(async () => {
      try {
        await aliasManager.initialize();
        const templates = await aliasManager.listTemplates();

        if (templates.length === 0) {
          console.log(chalk.yellow('No templates found'));
          return;
        }

        console.log(chalk.bold('\nAlias Templates:'));
        console.log(chalk.gray('─'.repeat(80)));

        templates.forEach(template => {
          console.log(chalk.cyan(`\n${template.name}`));
          if (template.description) {
            console.log(chalk.gray(`  ${template.description}`));
          }
          console.log(chalk.white(`  Query: ${template.query}`));

          if (template.parameters && template.parameters.length > 0) {
            console.log(chalk.gray('  Parameters:'));
            template.parameters.forEach((p, i) => {
              console.log(chalk.gray(`    $${i + 1}: ${p.name} (${p.type})`));
            });
          }

          if (template.tags && template.tags.length > 0) {
            console.log(chalk.gray(`  Tags: ${template.tags.join(', ')}`));
          }
        });

        console.log(chalk.gray('\n' + '─'.repeat(80)));
        console.log(chalk.gray(`Total: ${templates.length} templates\n`));
      } catch (error) {
        console.error(chalk.red(`Error: ${(error as Error).message}`));
        process.exit(1);
      }
    });

  template
    .command('create <name>')
    .description('Create a new template')
    .requiredOption('-q, --query <query>', 'Template query')
    .option('-d, --description <text>', 'Template description')
    .option('-p, --parameters <list>', 'Template parameters')
    .option('-t, --tags <tags>', 'Comma-separated tags')
    .action(async (name: string, options: {
      query: string;
      description?: string;
      parameters?: string;
      tags?: string;
    }) => {
      try {
        await aliasManager.initialize();

        const params = options.parameters
          ? (aliasManager as any).parseParameters(options.parameters)
          : undefined;

        const tags = options.tags ? options.tags.split(',').map(t => t.trim()) : undefined;

        await aliasManager.createTemplate({
          name,
          description: options.description || '',
          query: options.query,
          parameters: params,
          tags
        });

        console.log(chalk.green(`✓ Template '${name}' created successfully`));
      } catch (error) {
        console.error(chalk.red(`Error: ${(error as Error).message}`));
        process.exit(1);
      }
    });

  // alias from-template
  alias
    .command('from-template <template> <alias-name>')
    .description('Create an alias from a template')
    .action(async (template: string, aliasName: string) => {
      try {
        await aliasManager.initialize();
        await aliasManager.fromTemplate(template, aliasName);
        console.log(chalk.green(`✓ Alias '${aliasName}' created from template '${template}'`));
      } catch (error) {
        console.error(chalk.red(`Error: ${(error as Error).message}`));
        process.exit(1);
      }
    });

  // alias stats
  alias
    .command('stats')
    .description('Show alias usage statistics')
    .action(async () => {
      try {
        await aliasManager.initialize();
        const stats = await aliasManager.getStatistics();

        console.log(chalk.bold('\nAlias Statistics:'));
        console.log(chalk.gray('─'.repeat(80)));

        console.log(chalk.white(`Total aliases: ${stats.totalAliases}`));
        console.log(chalk.white(`Total usage: ${stats.totalUsage}`));

        if (stats.mostUsed.length > 0) {
          console.log(chalk.cyan('\nMost Used:'));
          stats.mostUsed.forEach((alias, i) => {
            console.log(chalk.gray(`  ${i + 1}. ${alias.name} (${alias.usageCount} times)`));
          });
        }

        if (stats.leastUsed.length > 0 && stats.totalAliases > 5) {
          console.log(chalk.yellow('\nLeast Used:'));
          stats.leastUsed.forEach((alias, i) => {
            console.log(chalk.gray(`  ${i + 1}. ${alias.name} (${alias.usageCount} times)`));
          });
        }

        if (stats.recentlyCreated.length > 0) {
          console.log(chalk.green('\nRecently Created:'));
          stats.recentlyCreated.forEach((alias, i) => {
            console.log(chalk.gray(`  ${i + 1}. ${alias.name} (${alias.createdAt.toLocaleDateString()})`));
          });
        }

        console.log(chalk.gray('\n' + '─'.repeat(80) + '\n'));
      } catch (error) {
        console.error(chalk.red(`Error: ${(error as Error).message}`));
        process.exit(1);
      }
    });
}
