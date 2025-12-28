#!/usr/bin/env node

/**
 * Generate 30-minute progress report
 * Reads test data and updates the live dashboard
 */

const fs = require('fs');
const path = require('path');

const LOG_DIR = '/home/claude/AIShell/aishell/tests/logs';
const REPORT_FILE = '/home/claude/AIShell/aishell/docs/reports/coverage-tracking-live.md';
const CSV_FILE = path.join(LOG_DIR, 'progress-tracking.csv');

// Read CSV data
function readProgressData() {
  if (!fs.existsSync(CSV_FILE)) {
    return [];
  }

  const content = fs.readFileSync(CSV_FILE, 'utf-8');
  const lines = content.trim().split('\n').slice(1); // Skip header

  return lines.map(line => {
    const [timestamp, passing, failing, skipped, percentage] = line.split(',');
    return {
      timestamp,
      passing: parseInt(passing),
      failing: parseInt(failing),
      skipped: parseInt(skipped),
      percentage: parseFloat(percentage)
    };
  });
}

// Calculate velocity
function calculateVelocity(data) {
  if (data.length < 2) return 0;

  const first = data[0];
  const last = data[data.length - 1];

  const timeDiff = new Date(last.timestamp) - new Date(first.timestamp);
  const hoursDiff = timeDiff / (1000 * 60 * 60);

  const testDiff = last.passing - first.passing;

  return hoursDiff > 0 ? testDiff / hoursDiff : 0;
}

// Calculate ETA
function calculateETA(currentPassing, velocity) {
  const target = 1520; // 95% of 1600
  const needed = target - currentPassing;

  if (velocity <= 0) return 'TBD';

  const hoursNeeded = needed / velocity;
  return `${hoursNeeded.toFixed(1)} hours`;
}

// Generate progress bar
function generateProgressBar(percentage) {
  const width = 50;
  const filled = Math.round((percentage / 100) * width);
  const empty = width - filled;

  return `[${'='.repeat(filled)}>${' '.repeat(empty)}] ${percentage.toFixed(2)}%`;
}

// Generate timeline table
function generateTimeline(data) {
  const rows = data.slice(-10).map((entry, index) => {
    const change = index > 0 ? entry.passing - data[data.length - 10 + index - 1].passing : 0;
    const changeStr = change > 0 ? `+${change}` : change < 0 ? change : '--';
    return `${entry.timestamp} | ${entry.passing}/1600      | ${changeStr.padStart(6)} | --        | --`;
  });

  return rows.join('\n');
}

// Update dashboard
function updateDashboard() {
  const data = readProgressData();

  if (data.length === 0) {
    console.log('No progress data available yet');
    return;
  }

  const latest = data[data.length - 1];
  const velocity = calculateVelocity(data);
  const eta = calculateETA(latest.passing, velocity);
  const progressBar = generateProgressBar(latest.percentage);
  const timeline = generateTimeline(data);

  const now = new Date().toISOString().replace('T', ' ').substring(0, 19);

  // Read current report
  let report = fs.readFileSync(REPORT_FILE, 'utf-8');

  // Update timestamp
  report = report.replace(
    /\*\*Last Updated:\*\* .*/,
    `**Last Updated:** ${now}`
  );

  // Update current stats
  report = report.replace(
    /Current:  \d+\/1600 tests passing \([\d.]+%\)/,
    `Current:  ${latest.passing}/1600 tests passing (${latest.percentage.toFixed(2)}%)`
  );

  report = report.replace(
    /Gap:      \d+ tests needed/,
    `Gap:      ${1520 - latest.passing} tests needed`
  );

  report = report.replace(
    /Failed:   \d+ tests/,
    `Failed:   ${latest.failing} tests`
  );

  report = report.replace(
    /Skipped:  \d+ tests/,
    `Skipped:  ${latest.skipped} tests`
  );

  // Update progress bar
  report = report.replace(
    /\[=*>?\s*\] [\d.]+%/,
    progressBar
  );

  // Update velocity section
  const velocitySection = `### Progress Timeline
\`\`\`
Time     | Tests Passing | Change | Rate      | ETA to 95%
---------|---------------|--------|-----------|------------
${timeline}
\`\`\`

### Projected Timeline
- **Tests Needed:** ${1520 - latest.passing} tests
- **Expected Velocity:** ${velocity > 0 ? velocity.toFixed(1) + ' tests/hour' : 'TBD (awaiting agent completions)'}
- **ETA to 95%:** ${eta}`;

  report = report.replace(
    /### Progress Timeline[\s\S]*?### Projected Timeline[\s\S]*?---/,
    velocitySection + '\n\n---'
  );

  // Write updated report
  fs.writeFileSync(REPORT_FILE, report);

  console.log(`Dashboard updated at ${now}`);
  console.log(`Current: ${latest.passing}/1600 (${latest.percentage.toFixed(2)}%)`);
  console.log(`Velocity: ${velocity > 0 ? velocity.toFixed(1) + ' tests/hour' : 'TBD'}`);
  console.log(`ETA: ${eta}`);
}

// Run update
try {
  updateDashboard();
} catch (error) {
  console.error('Error updating dashboard:', error);
  process.exit(1);
}
