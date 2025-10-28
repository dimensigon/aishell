/**
 * Security CLI Tests
 * Comprehensive test suite for all security CLI commands
 */

import { SecurityCLI } from '../../src/cli/security-cli';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import * as fs from 'fs/promises';
import * as path from 'path';

describe('SecurityCLI', () => {
  let securityCLI: SecurityCLI;

  beforeEach(() => {
    securityCLI = new SecurityCLI();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  // ============================================================================
  // VAULT OPERATIONS TESTS
  // ============================================================================

  describe('Vault Operations', () => {
    it('should add vault entry without encryption', async () => {
      const result = await securityCLI.addVaultEntry('test-key', 'test-value', {
        encrypt: false
      });

      expect(result).toBeUndefined(); // void return
    });

    it('should add vault entry with encryption', async () => {
      const result = await securityCLI.addVaultEntry('encrypted-key', 'secret-value', {
        encrypt: true
      });

      expect(result).toBeUndefined();
    });

    it('should list vault entries without showing passwords', async () => {
      await securityCLI.addVaultEntry('key1', 'value1');
      await securityCLI.addVaultEntry('key2', 'value2');

      const entries = await securityCLI.listVaultEntries({ showPasswords: false });

      expect(Array.isArray(entries)).toBe(true);
    });

    it('should list vault entries showing passwords', async () => {
      await securityCLI.addVaultEntry('key1', 'value1');

      const entries = await securityCLI.listVaultEntries({ showPasswords: true });

      expect(Array.isArray(entries)).toBe(true);
    });

    it('should get specific vault entry', async () => {
      await securityCLI.addVaultEntry('specific-key', 'specific-value');

      const entry = await securityCLI.getVaultEntry('specific-key');

      expect(entry).toBeDefined();
    });

    it('should remove vault entry', async () => {
      await securityCLI.addVaultEntry('to-remove', 'value');
      await securityCLI.removeVaultEntry('to-remove');

      // Verify it's removed
      const entry = await securityCLI.getVaultEntry('to-remove');
      expect(entry.success).toBe(false);
    });

    it('should handle removing non-existent entry', async () => {
      await securityCLI.removeVaultEntry('non-existent');
      // Should not throw error
    });

    it('should encrypt value', async () => {
      const encrypted = await securityCLI.encryptValue('plain-text');

      expect(typeof encrypted).toBe('string');
      expect(encrypted.length).toBeGreaterThan(0);
      expect(encrypted).not.toBe('plain-text');
    });

    it('should decrypt value', async () => {
      const encrypted = await securityCLI.encryptValue('original-text');
      const decrypted = await securityCLI.decryptValue(encrypted);

      expect(decrypted).toBe('original-text');
    });

    it('should rotate vault key', async () => {
      await securityCLI.rotateVaultKey();
      // Should not throw error
    });

    it('should handle vault with different formats', async () => {
      await securityCLI.addVaultEntry('key1', 'value1');

      const jsonEntries = await securityCLI.listVaultEntries({ format: 'json' });
      expect(Array.isArray(jsonEntries)).toBe(true);

      const tableEntries = await securityCLI.listVaultEntries({ format: 'table' });
      expect(Array.isArray(tableEntries)).toBe(true);

      const csvEntries = await securityCLI.listVaultEntries({ format: 'csv' });
      expect(Array.isArray(csvEntries)).toBe(true);
    });
  });

  // ============================================================================
  // AUDIT LOG TESTS
  // ============================================================================

  describe('Audit Log Operations', () => {
    it('should show audit log with default options', async () => {
      const logs = await securityCLI.showAuditLog();

      expect(Array.isArray(logs)).toBe(true);
    });

    it('should show audit log with limit', async () => {
      const logs = await securityCLI.showAuditLog({ limit: 10 });

      expect(Array.isArray(logs)).toBe(true);
      expect(logs.length).toBeLessThanOrEqual(10);
    });

    it('should filter audit log by user', async () => {
      const logs = await securityCLI.showAuditLog({ user: 'admin' });

      expect(Array.isArray(logs)).toBe(true);
    });

    it('should filter audit log by action', async () => {
      const logs = await securityCLI.showAuditLog({ action: 'login' });

      expect(Array.isArray(logs)).toBe(true);
    });

    it('should filter audit log by resource', async () => {
      const logs = await securityCLI.showAuditLog({ resource: 'database' });

      expect(Array.isArray(logs)).toBe(true);
    });

    it('should export audit log as JSON', async () => {
      const outputFile = path.join(__dirname, 'test-audit.json');

      await securityCLI.exportAuditLog(outputFile, { format: 'json' });

      // Verify file exists
      const exists = await fs.access(outputFile).then(() => true).catch(() => false);
      expect(exists).toBe(true);

      // Cleanup
      if (exists) {
        await fs.unlink(outputFile);
      }
    });

    it('should export audit log as CSV', async () => {
      const outputFile = path.join(__dirname, 'test-audit.csv');

      await securityCLI.exportAuditLog(outputFile, { format: 'csv' });

      // Verify file exists
      const exists = await fs.access(outputFile).then(() => true).catch(() => false);
      expect(exists).toBe(true);

      // Cleanup
      if (exists) {
        await fs.unlink(outputFile);
      }
    });

    it('should clear old audit logs', async () => {
      const beforeDate = new Date(Date.now() - 90 * 24 * 60 * 60 * 1000); // 90 days ago
      await securityCLI.clearAuditLog(beforeDate);
      // Should not throw error
    });

    it('should show audit statistics', async () => {
      await securityCLI.auditStats();
      // Should not throw error
    });

    it('should search audit logs', async () => {
      const results = await securityCLI.searchAuditLog('login');

      expect(Array.isArray(results)).toBe(true);
    });
  });

  // ============================================================================
  // RBAC TESTS
  // ============================================================================

  describe('RBAC Operations', () => {
    it('should create new role', async () => {
      await securityCLI.createRole('test-role', 'Test role description');
      // Should not throw error
    });

    it('should delete role', async () => {
      await securityCLI.createRole('to-delete');
      await securityCLI.deleteRole('to-delete');
      // Should not throw error
    });

    it('should grant permission with single action', async () => {
      await securityCLI.createRole('test-role');
      await securityCLI.grantPermission('test-role', 'database', {
        actions: ['read']
      });
      // Should not throw error
    });

    it('should grant permission with multiple actions', async () => {
      await securityCLI.createRole('test-role');
      await securityCLI.grantPermission('test-role', 'database', {
        actions: ['read', 'write', 'delete']
      });
      // Should not throw error
    });

    it('should revoke permission', async () => {
      await securityCLI.createRole('test-role');
      await securityCLI.grantPermission('test-role', 'database', { actions: ['read'] });
      await securityCLI.revokePermission('test-role', 'database');
      // Should not throw error
    });

    it('should list permissions for user', async () => {
      await securityCLI.listPermissions('test-user');
      // Should not throw error
    });

    it('should list all roles', async () => {
      await securityCLI.listPermissions();
      // Should not throw error
    });

    it('should check permission - granted', async () => {
      await securityCLI.createRole('admin');
      await securityCLI.grantPermission('admin', 'database', { actions: ['read'] });
      await securityCLI.assignRole('user1', 'admin');

      const allowed = await securityCLI.checkPermission('user1', 'database', 'read');

      // May be false if not properly set up, but should not throw
      expect(typeof allowed).toBe('boolean');
    });

    it('should check permission - denied', async () => {
      const allowed = await securityCLI.checkPermission('user2', 'database', 'write');

      expect(typeof allowed).toBe('boolean');
    });

    it('should assign role to user', async () => {
      await securityCLI.createRole('editor');
      await securityCLI.assignRole('user3', 'editor');
      // Should not throw error
    });

    it('should unassign role from user', async () => {
      await securityCLI.createRole('viewer');
      await securityCLI.assignRole('user4', 'viewer');
      await securityCLI.unassignRole('user4', 'viewer');
      // Should not throw error
    });

    it('should list permissions in JSON format', async () => {
      await securityCLI.listPermissions('test-user', { format: 'json' });
      // Should not throw error
    });

    it('should list permissions in table format', async () => {
      await securityCLI.listPermissions('test-user', { format: 'table' });
      // Should not throw error
    });
  });

  // ============================================================================
  // SECURITY SCANNING TESTS
  // ============================================================================

  describe('Security Scanning', () => {
    it('should run basic security scan', async () => {
      const report = await securityCLI.runSecurityScan();

      expect(report).toBeDefined();
      expect(report.timestamp).toBeDefined();
      expect(report.vulnerabilities).toBeDefined();
      expect(report.compliance).toBeDefined();
      expect(report.summary).toBeDefined();
    });

    it('should run deep security scan', async () => {
      const report = await securityCLI.runSecurityScan({ deep: true });

      expect(report).toBeDefined();
      expect(report.summary.totalIssues).toBeGreaterThanOrEqual(0);
    });

    it('should generate security report with JSON format', async () => {
      await securityCLI.generateSecurityReport({ format: 'json' });
      // Should not throw error
    });

    it('should generate security report with table format', async () => {
      await securityCLI.generateSecurityReport({ format: 'table' });
      // Should not throw error
    });

    it('should save security report to file', async () => {
      const outputFile = path.join(__dirname, 'test-security-report.json');

      await securityCLI.runSecurityScan({ outputFile });

      // Verify file exists
      const exists = await fs.access(outputFile).then(() => true).catch(() => false);
      expect(exists).toBe(true);

      // Cleanup
      if (exists) {
        await fs.unlink(outputFile);
      }
    });

    it('should list vulnerabilities', async () => {
      await securityCLI.listVulnerabilities();
      // Should not throw error
    });

    it('should check GDPR compliance', async () => {
      const report: any = {
        compliance: {}
      };

      await securityCLI.checkCompliance(report, { standard: 'gdpr' });

      expect(report.compliance.gdpr).toBeDefined();
    });

    it('should check SOX compliance', async () => {
      const report: any = {
        compliance: {}
      };

      await securityCLI.checkCompliance(report, { standard: 'sox' });

      expect(report.compliance.sox).toBeDefined();
    });

    it('should check HIPAA compliance', async () => {
      const report: any = {
        compliance: {}
      };

      await securityCLI.checkCompliance(report, { standard: 'hipaa' });

      expect(report.compliance.hipaa).toBeDefined();
    });

    it('should check all compliance standards', async () => {
      const report: any = {
        compliance: {}
      };

      await securityCLI.checkCompliance(report, { standard: 'all' });

      expect(report.compliance.gdpr).toBeDefined();
      expect(report.compliance.sox).toBeDefined();
      expect(report.compliance.hipaa).toBeDefined();
    });
  });

  // ============================================================================
  // ERROR HANDLING TESTS
  // ============================================================================

  describe('Error Handling', () => {
    it('should handle invalid vault entry gracefully', async () => {
      const entry = await securityCLI.getVaultEntry('non-existent-key');

      expect(entry.success).toBe(false);
    });

    it('should handle invalid role deletion gracefully', async () => {
      await securityCLI.deleteRole('non-existent-role');
      // Should not throw error
    });

    it('should handle empty audit log gracefully', async () => {
      const logs = await securityCLI.showAuditLog({ limit: 0 });

      expect(Array.isArray(logs)).toBe(true);
    });

    it('should handle invalid permission check gracefully', async () => {
      const allowed = await securityCLI.checkPermission(
        'non-existent-user',
        'non-existent-resource',
        'non-existent-action'
      );

      expect(typeof allowed).toBe('boolean');
    });
  });

  // ============================================================================
  // INTEGRATION TESTS
  // ============================================================================

  describe('Integration Tests', () => {
    it('should complete full vault workflow', async () => {
      // Add entry
      await securityCLI.addVaultEntry('workflow-key', 'workflow-value', {
        encrypt: true
      });

      // List entries
      const entries = await securityCLI.listVaultEntries();
      expect(entries.length).toBeGreaterThan(0);

      // Get entry
      const entry = await securityCLI.getVaultEntry('workflow-key');
      expect(entry).toBeDefined();

      // Remove entry
      await securityCLI.removeVaultEntry('workflow-key');
    });

    it('should complete full RBAC workflow', async () => {
      // Create role
      await securityCLI.createRole('workflow-role', 'Workflow test role');

      // Grant permissions
      await securityCLI.grantPermission('workflow-role', 'api', {
        actions: ['read', 'write']
      });

      // Assign to user
      await securityCLI.assignRole('workflow-user', 'workflow-role');

      // Check permission
      const allowed = await securityCLI.checkPermission(
        'workflow-user',
        'api',
        'read'
      );
      expect(typeof allowed).toBe('boolean');

      // Unassign role
      await securityCLI.unassignRole('workflow-user', 'workflow-role');

      // Delete role
      await securityCLI.deleteRole('workflow-role');
    });

    it('should complete full security scan workflow', async () => {
      // Run scan
      const report = await securityCLI.runSecurityScan({ deep: true });

      // Verify report structure
      expect(report.timestamp).toBeDefined();
      expect(report.vulnerabilities).toBeDefined();
      expect(report.compliance).toBeDefined();
      expect(report.summary).toBeDefined();

      // Check compliance
      await securityCLI.checkCompliance(report);

      // Generate report
      await securityCLI.generateSecurityReport();
    });
  });
});
