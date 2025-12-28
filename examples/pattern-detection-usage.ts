/**
 * Pattern Detection Usage Examples
 * Complete guide to using the Advanced Pattern Detection System
 */

import { PatternDetector, PatternType } from '../src/cli/pattern-detection';
import { QueryLogger } from '../src/cli/query-logger';
import { StateManager } from '../src/core/state-manager';

// ============================================================================
// Example 1: Basic Pattern Analysis
// ============================================================================

async function basicPatternAnalysis() {
  console.log('=== Example 1: Basic Pattern Analysis ===\n');

  // Initialize components
  const stateManager = new StateManager('./data/state.db');
  const queryLogger = new QueryLogger(stateManager);
  const detector = new PatternDetector(stateManager, queryLogger);

  // Analyze last 7 days
  const insights = await detector.analyze({ period: 7 });

  console.log(`Patterns found: ${insights.summary.totalPatterns}`);
  console.log(`Anomalies detected: ${insights.summary.anomaliesDetected}`);
  console.log(`Security threats: ${insights.summary.securityThreats}`);
  console.log(`Confidence: ${(insights.confidence * 100).toFixed(1)}%\n`);

  // Generate report
  const report = await detector.report({ format: 'summary' });
  console.log(report);
}

// ============================================================================
// Example 2: Security Monitoring with Real-time Alerts
// ============================================================================

async function securityMonitoring() {
  console.log('=== Example 2: Security Monitoring ===\n');

  const stateManager = new StateManager('./data/state.db');
  const queryLogger = new QueryLogger(stateManager);

  // Configure for security
  const detector = new PatternDetector(
    stateManager,
    queryLogger,
    {
      securityScanEnabled: true,
      anomalyThreshold: 0.65, // More sensitive
      aiAnalysisEnabled: true
    },
    process.env.ANTHROPIC_API_KEY
  );

  // Set up event listeners
  detector.on('securityThreat', async (threat) => {
    console.log('🚨 SECURITY THREAT DETECTED');
    console.log('─────────────────────────────────────');
    console.log(`Type: ${threat.threatType}`);
    console.log(`Confidence: ${(threat.confidence * 100).toFixed(1)}%`);
    console.log(`Query: ${threat.query.substring(0, 100)}...`);
    console.log(`Indicators: ${threat.indicators.join(', ')}`);
    console.log(`Recommendation: ${threat.recommendation}`);
    console.log('');

    // Send alert (example)
    await sendSecurityAlert({
      level: threat.confidence > 0.8 ? 'critical' : 'high',
      type: threat.threatType,
      query: threat.query,
      timestamp: threat.timestamp,
      indicators: threat.indicators
    });
  });

  detector.on('anomalyDetected', (anomaly) => {
    if (anomaly.severity === 'critical' || anomaly.severity === 'high') {
      console.log(`⚠️  ${anomaly.severity.toUpperCase()} anomaly detected`);
      console.log(`   Type: ${anomaly.type}`);
      console.log(`   Score: ${anomaly.anomalyScore.toFixed(2)}`);
      console.log(`   Reasons: ${anomaly.reasons.join(', ')}\n`);
    }
  });

  // Continuous monitoring
  console.log('Starting continuous security monitoring...');
  setInterval(async () => {
    const insights = await detector.analyze({ period: 1 });

    if (insights.summary.securityThreats > 0) {
      console.log(`[${new Date().toISOString()}] ${insights.summary.securityThreats} new threats detected`);
    }
  }, 60000); // Check every minute
}

// ============================================================================
// Example 3: Performance Optimization Analysis
// ============================================================================

async function performanceOptimization() {
  console.log('=== Example 3: Performance Optimization ===\n');

  const stateManager = new StateManager('./data/state.db');
  const queryLogger = new QueryLogger(stateManager);
  const detector = new PatternDetector(
    stateManager,
    queryLogger,
    { aiAnalysisEnabled: true },
    process.env.ANTHROPIC_API_KEY
  );

  // Analyze performance patterns over 30 days
  const insights = await detector.analyze({
    period: 30,
    types: [PatternType.PERFORMANCE]
  });

  console.log('Performance Analysis Results');
  console.log('═══════════════════════════════════════\n');

  // Slow query patterns
  const slowPatterns = insights.patterns.filter(
    p => p.type === PatternType.PERFORMANCE && p.avgPerformance > 1000
  );

  console.log(`Found ${slowPatterns.length} slow query patterns:\n`);

  for (const pattern of slowPatterns) {
    console.log(`Pattern: ${pattern.id}`);
    console.log(`  Frequency: ${pattern.frequency} queries`);
    console.log(`  Avg Performance: ${pattern.avgPerformance.toFixed(2)}ms`);
    console.log(`  Characteristics: ${pattern.characteristics.join(', ')}`);

    if (pattern.recommendations) {
      console.log(`  Recommendations:`);
      pattern.recommendations.forEach(rec => {
        console.log(`    • ${rec}`);
      });
    }
    console.log('');
  }

  // Performance trends
  console.log('Performance Trends:');
  insights.performancePatterns.forEach(perf => {
    console.log(`\n${perf.description}`);
    console.log(`  Trend: ${perf.trend.toUpperCase()}`);
    console.log(`  Queries Affected: ${perf.queriesAffected}`);
    console.log(`  Avg Impact: ${perf.avgImpact.toFixed(2)}ms`);
    console.log(`  Recommendations:`);
    perf.recommendations.forEach(rec => {
      console.log(`    • ${rec}`);
    });
  });

  // Export for further analysis
  await detector.export('./reports/slow-patterns.json');
  console.log('\n✓ Detailed analysis exported to ./reports/slow-patterns.json');
}

// ============================================================================
// Example 4: Automated Learning and Optimization
// ============================================================================

async function automatedLearning() {
  console.log('=== Example 4: Automated Learning ===\n');

  const stateManager = new StateManager('./data/state.db');
  const queryLogger = new QueryLogger(stateManager);
  const detector = new PatternDetector(
    stateManager,
    queryLogger,
    {
      learningEnabled: true,
      aiAnalysisEnabled: true
    },
    process.env.ANTHROPIC_API_KEY
  );

  // Daily analysis and learning workflow
  async function dailyAnalysis() {
    console.log(`[${new Date().toISOString()}] Starting daily pattern analysis...`);

    // Step 1: Analyze patterns
    const insights = await detector.analyze({ period: 1 });

    console.log('Daily Analysis Results:');
    console.log(`  - Patterns: ${insights.summary.totalPatterns}`);
    console.log(`  - Anomalies: ${insights.summary.anomaliesDetected}`);
    console.log(`  - Security Threats: ${insights.summary.securityThreats}`);
    console.log(`  - Performance Issues: ${insights.summary.performanceIssues}`);

    // Step 2: Learn from patterns
    await detector.learn();
    console.log('  - Learning model updated');

    // Step 3: Generate and send report
    const report = await detector.report({
      format: 'detailed',
      includeRecommendations: true
    });

    await sendDailyReport(report);
    console.log('  - Daily report sent');

    // Step 4: Export data
    const timestamp = new Date().toISOString().split('T')[0];
    await detector.export(`./archives/patterns-${timestamp}.json`);
    console.log(`  - Data archived: patterns-${timestamp}.json\n`);
  }

  // Run daily at 2 AM
  const cron = require('node-cron');
  cron.schedule('0 2 * * *', dailyAnalysis);

  console.log('Automated learning system started');
  console.log('Daily analysis scheduled for 2:00 AM');
}

// ============================================================================
// Example 5: Comprehensive Multi-Stage Analysis Pipeline
// ============================================================================

async function comprehensiveAnalysisPipeline() {
  console.log('=== Example 5: Comprehensive Analysis Pipeline ===\n');

  const stateManager = new StateManager('./data/state.db');
  const queryLogger = new QueryLogger(stateManager);
  const detector = new PatternDetector(
    stateManager,
    queryLogger,
    { aiAnalysisEnabled: true },
    process.env.ANTHROPIC_API_KEY
  );

  // Stage 1: Security Analysis
  console.log('Stage 1/4: Security Analysis');
  console.log('─────────────────────────────────────');
  const securityInsights = await detector.analyze({
    period: 7,
    types: [PatternType.SECURITY]
  });

  if (securityInsights.summary.securityThreats > 0) {
    console.log(`⚠️  Found ${securityInsights.summary.securityThreats} security threats`);
    await handleSecurityThreats(securityInsights.securityThreats);
  } else {
    console.log('✓ No security threats detected');
  }
  console.log('');

  // Stage 2: Performance Analysis
  console.log('Stage 2/4: Performance Analysis');
  console.log('─────────────────────────────────────');
  const perfInsights = await detector.analyze({
    period: 30,
    types: [PatternType.PERFORMANCE]
  });

  const optimizations = generateOptimizations(perfInsights);
  console.log(`Found ${optimizations.length} optimization opportunities`);

  if (optimizations.length > 0) {
    console.log('Applying optimizations...');
    await applyOptimizations(optimizations);
    console.log('✓ Optimizations applied');
  }
  console.log('');

  // Stage 3: Usage Analysis
  console.log('Stage 3/4: Usage Analysis');
  console.log('─────────────────────────────────────');
  const usageInsights = await detector.analyze({
    period: 90,
    types: [PatternType.USAGE]
  });

  const capacityPlan = generateCapacityPlan(usageInsights);
  console.log('Capacity planning recommendations:');
  capacityPlan.forEach(rec => {
    console.log(`  • ${rec}`);
  });

  await updateCapacityPlan(capacityPlan);
  console.log('✓ Capacity plan updated');
  console.log('');

  // Stage 4: Learning and Export
  console.log('Stage 4/4: Learning and Export');
  console.log('─────────────────────────────────────');
  await detector.learn();
  console.log('✓ Pattern learning complete');

  await detector.export('./reports/comprehensive-analysis.json');
  console.log('✓ Analysis exported');
  console.log('');

  // Generate comprehensive report
  const report = await detector.report({
    format: 'detailed',
    includeRecommendations: true
  });

  console.log('Comprehensive Analysis Complete');
  console.log('═══════════════════════════════════════\n');
  console.log(report);

  return report;
}

// ============================================================================
// Example 6: Real-time Monitoring Dashboard
// ============================================================================

async function realtimeMonitoringDashboard() {
  console.log('=== Example 6: Real-time Monitoring Dashboard ===\n');

  const stateManager = new StateManager('./data/state.db');
  const queryLogger = new QueryLogger(stateManager);
  const detector = new PatternDetector(stateManager, queryLogger);

  // Dashboard state
  let dashboardData = {
    patterns: 0,
    anomalies: 0,
    threats: 0,
    performance: 'stable' as 'improving' | 'degrading' | 'stable'
  };

  // Listen for all events
  detector.on('patternDiscovered', (pattern) => {
    dashboardData.patterns++;
    updateDashboard();
  });

  detector.on('anomalyDetected', (anomaly) => {
    dashboardData.anomalies++;
    if (anomaly.severity === 'critical') {
      console.log(`\n🚨 CRITICAL ANOMALY: ${anomaly.query.substring(0, 50)}...`);
    }
    updateDashboard();
  });

  detector.on('securityThreat', (threat) => {
    dashboardData.threats++;
    console.log(`\n🔒 SECURITY THREAT: ${threat.threatType}`);
    updateDashboard();
  });

  detector.on('analysisComplete', (insights) => {
    const perfPattern = insights.performancePatterns[0];
    if (perfPattern) {
      dashboardData.performance = perfPattern.trend;
    }
    updateDashboard();
  });

  function updateDashboard() {
    console.clear();
    console.log('═══════════════════════════════════════════════════════');
    console.log('           PATTERN DETECTION DASHBOARD');
    console.log('═══════════════════════════════════════════════════════');
    console.log(`Timestamp: ${new Date().toISOString()}\n`);
    console.log(`📊 Patterns Discovered: ${dashboardData.patterns}`);
    console.log(`⚠️  Anomalies Detected: ${dashboardData.anomalies}`);
    console.log(`🔒 Security Threats: ${dashboardData.threats}`);
    console.log(`📈 Performance Trend: ${dashboardData.performance.toUpperCase()}\n`);
    console.log('═══════════════════════════════════════════════════════');
    console.log('Press Ctrl+C to stop monitoring');
  }

  // Initial update
  updateDashboard();

  // Periodic analysis
  setInterval(async () => {
    await detector.analyze({ period: 1 });
  }, 60000); // Every minute
}

// ============================================================================
// Helper Functions
// ============================================================================

async function sendSecurityAlert(alert: any): Promise<void> {
  // Implementation: Send email, Slack notification, etc.
  console.log(`[ALERT] Security alert sent: ${alert.type}`);
}

async function sendDailyReport(report: string): Promise<void> {
  // Implementation: Email report to team
  console.log('[REPORT] Daily report sent to team');
}

async function handleSecurityThreats(threats: any[]): Promise<void> {
  // Implementation: Review and respond to threats
  for (const threat of threats) {
    console.log(`  Handling threat: ${threat.threatType}`);
    // Take appropriate action
  }
}

function generateOptimizations(insights: any): any[] {
  // Implementation: Generate optimization commands
  const optimizations: any[] = [];

  for (const pattern of insights.patterns) {
    if (pattern.avgPerformance > 1000) {
      optimizations.push({
        type: 'index',
        target: pattern.queries[0],
        recommendation: 'Add index on frequently queried columns'
      });
    }
  }

  return optimizations;
}

async function applyOptimizations(optimizations: any[]): Promise<void> {
  // Implementation: Apply database optimizations
  for (const opt of optimizations) {
    console.log(`  Applying: ${opt.recommendation}`);
    // Execute optimization
  }
}

function generateCapacityPlan(insights: any): string[] {
  // Implementation: Generate capacity recommendations
  const recommendations: string[] = [];

  if (insights.usagePatterns.peakHours.length > 0) {
    recommendations.push(
      `Scale up during peak hours: ${insights.usagePatterns.peakHours.map((h: any) => h.hour).join(', ')}`
    );
  }

  return recommendations;
}

async function updateCapacityPlan(plan: string[]): Promise<void> {
  // Implementation: Update infrastructure capacity
  console.log('Capacity plan updated');
}

// ============================================================================
// Main Execution
// ============================================================================

async function main() {
  const examples = [
    { name: 'Basic Pattern Analysis', fn: basicPatternAnalysis },
    { name: 'Security Monitoring', fn: securityMonitoring },
    { name: 'Performance Optimization', fn: performanceOptimization },
    { name: 'Automated Learning', fn: automatedLearning },
    { name: 'Comprehensive Pipeline', fn: comprehensiveAnalysisPipeline },
    { name: 'Real-time Dashboard', fn: realtimeMonitoringDashboard }
  ];

  console.log('Pattern Detection Usage Examples');
  console.log('═══════════════════════════════════════════════════════\n');

  for (let i = 0; i < examples.length; i++) {
    console.log(`${i + 1}. ${examples[i].name}`);
  }

  console.log('\nSelect an example to run (1-6), or 0 to exit:');

  // For demo purposes, run example 1
  await basicPatternAnalysis();
}

// Run if executed directly
if (require.main === module) {
  main().catch(console.error);
}

// Export functions for use in other modules
export {
  basicPatternAnalysis,
  securityMonitoring,
  performanceOptimization,
  automatedLearning,
  comprehensiveAnalysisPipeline,
  realtimeMonitoringDashboard
};
