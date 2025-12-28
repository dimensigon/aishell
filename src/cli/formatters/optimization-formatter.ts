/**
 * Optimization Result Formatter
 * Formats query optimization results in various formats
 */

import chalk from 'chalk';
import Table from 'cli-table3';

export interface OptimizationResult {
  originalQuery: string;
  optimizedQuery: string;
  issues: string[];
  suggestions: string[];
  indexRecommendations: string[];
  estimatedImprovement: string;
  executionPlanBefore?: any;
  executionPlanAfter?: any;
}

/**
 * Format optimization result based on specified format
 */
export function formatOptimizationResult(
  result: OptimizationResult,
  format: 'text' | 'json' | 'table' | 'csv'
): string {
  switch (format) {
    case 'json':
      return formatAsJSON(result);
    case 'csv':
      return formatAsCSV(result);
    case 'table':
      return formatAsTable(result);
    case 'text':
    default:
      return formatAsText(result);
  }
}

/**
 * Format as text (human-readable)
 */
function formatAsText(result: OptimizationResult): string {
  const lines: string[] = [];

  lines.push(chalk.cyan.bold('\n📊 Query Optimization Results\n'));

  // Original Query
  lines.push(chalk.bold('Original Query:'));
  lines.push(chalk.dim(formatQueryText(result.originalQuery)));
  lines.push('');

  // Optimized Query
  lines.push(chalk.bold('Optimized Query:'));
  lines.push(chalk.green(formatQueryText(result.optimizedQuery)));
  lines.push('');

  // Estimated Improvement
  lines.push(chalk.bold('Estimated Improvement: ') + chalk.yellow(result.estimatedImprovement));
  lines.push('');

  // Issues
  if (result.issues.length > 0) {
    lines.push(chalk.red.bold('⚠️  Issues Found:\n'));
    result.issues.forEach((issue, index) => {
      lines.push(chalk.red(`  ${index + 1}. ${issue}`));
    });
    lines.push('');
  }

  // Suggestions
  if (result.suggestions.length > 0) {
    lines.push(chalk.cyan.bold('💡 Suggestions:\n'));
    result.suggestions.forEach((suggestion, index) => {
      lines.push(chalk.cyan(`  ${index + 1}. ${suggestion}`));
    });
    lines.push('');
  }

  // Index Recommendations
  if (result.indexRecommendations.length > 0) {
    lines.push(chalk.green.bold('📈 Index Recommendations:\n'));
    result.indexRecommendations.forEach((rec, index) => {
      lines.push(chalk.green(`  ${index + 1}. ${rec}`));
    });
    lines.push('');
  }

  // Execution Plans
  if (result.executionPlanBefore && result.executionPlanAfter) {
    lines.push(chalk.bold('Execution Plans:'));
    lines.push('');
    lines.push(chalk.dim('Before:'));
    lines.push(chalk.dim(JSON.stringify(result.executionPlanBefore, null, 2)));
    lines.push('');
    lines.push(chalk.dim('After:'));
    lines.push(chalk.dim(JSON.stringify(result.executionPlanAfter, null, 2)));
    lines.push('');
  }

  return lines.join('\n');
}

/**
 * Format as JSON
 */
function formatAsJSON(result: OptimizationResult): string {
  return JSON.stringify(result, null, 2);
}

/**
 * Format as CSV
 */
function formatAsCSV(result: OptimizationResult): string {
  const rows: string[] = [];

  // Headers
  rows.push('Category,Item,Value');

  // Queries
  rows.push(`Query,Original,"${escapeCSV(result.originalQuery)}"`);
  rows.push(`Query,Optimized,"${escapeCSV(result.optimizedQuery)}"`);
  rows.push(`Query,Improvement,${result.estimatedImprovement}`);

  // Issues
  result.issues.forEach((issue, index) => {
    rows.push(`Issue,${index + 1},"${escapeCSV(issue)}"`);
  });

  // Suggestions
  result.suggestions.forEach((suggestion, index) => {
    rows.push(`Suggestion,${index + 1},"${escapeCSV(suggestion)}"`);
  });

  // Index recommendations
  result.indexRecommendations.forEach((rec, index) => {
    rows.push(`Index,${index + 1},"${escapeCSV(rec)}"`);
  });

  return rows.join('\n');
}

/**
 * Format as table
 */
function formatAsTable(result: OptimizationResult): string {
  const lines: string[] = [];

  // Summary table
  const summaryTable = new Table({
    head: [chalk.bold('Metric'), chalk.bold('Value')]
  });

  summaryTable.push(
    ['Original Query Length', result.originalQuery.length + ' characters'],
    ['Optimized Query Length', result.optimizedQuery.length + ' characters'],
    ['Estimated Improvement', chalk.yellow(result.estimatedImprovement)],
    ['Issues Found', chalk.red(result.issues.length.toString())],
    ['Suggestions', chalk.cyan(result.suggestions.length.toString())],
    ['Index Recommendations', chalk.green(result.indexRecommendations.length.toString())]
  );

  lines.push(chalk.cyan.bold('\n📊 Query Optimization Summary\n'));
  lines.push(summaryTable.toString());
  lines.push('');

  // Issues table
  if (result.issues.length > 0) {
    const issuesTable = new Table({
      head: [chalk.bold('#'), chalk.bold('Issue')],
      colWidths: [5, 75]
    });

    result.issues.forEach((issue, index) => {
      issuesTable.push([index + 1, chalk.red(issue)]);
    });

    lines.push(chalk.red.bold('⚠️  Issues:\n'));
    lines.push(issuesTable.toString());
    lines.push('');
  }

  // Suggestions table
  if (result.suggestions.length > 0) {
    const suggestionsTable = new Table({
      head: [chalk.bold('#'), chalk.bold('Suggestion')],
      colWidths: [5, 75]
    });

    result.suggestions.forEach((suggestion, index) => {
      suggestionsTable.push([index + 1, chalk.cyan(suggestion)]);
    });

    lines.push(chalk.cyan.bold('💡 Suggestions:\n'));
    lines.push(suggestionsTable.toString());
    lines.push('');
  }

  // Index recommendations table
  if (result.indexRecommendations.length > 0) {
    const indexTable = new Table({
      head: [chalk.bold('#'), chalk.bold('Index Recommendation')],
      colWidths: [5, 75]
    });

    result.indexRecommendations.forEach((rec, index) => {
      indexTable.push([index + 1, chalk.green(rec)]);
    });

    lines.push(chalk.green.bold('📈 Index Recommendations:\n'));
    lines.push(indexTable.toString());
    lines.push('');
  }

  // Queries
  lines.push(chalk.bold('Original Query:'));
  lines.push(chalk.dim(formatQueryText(result.originalQuery)));
  lines.push('');
  lines.push(chalk.bold('Optimized Query:'));
  lines.push(chalk.green(formatQueryText(result.optimizedQuery)));
  lines.push('');

  return lines.join('\n');
}

/**
 * Format query text with proper indentation
 */
function formatQueryText(query: string): string {
  return query
    .replace(/\s+/g, ' ')
    .replace(/\bSELECT\b/gi, '\nSELECT')
    .replace(/\bFROM\b/gi, '\nFROM')
    .replace(/\bWHERE\b/gi, '\nWHERE')
    .replace(/\bJOIN\b/gi, '\nJOIN')
    .replace(/\bGROUP BY\b/gi, '\nGROUP BY')
    .replace(/\bORDER BY\b/gi, '\nORDER BY')
    .replace(/\bHAVING\b/gi, '\nHAVING')
    .replace(/\bLIMIT\b/gi, '\nLIMIT')
    .trim()
    .split('\n')
    .map((line, index) => (index === 0 ? line : '  ' + line))
    .join('\n');
}

/**
 * Escape CSV value
 */
function escapeCSV(value: string): string {
  return value.replace(/"/g, '""').replace(/\n/g, ' ');
}
