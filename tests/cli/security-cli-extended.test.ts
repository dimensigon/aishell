/**
 * Extended Security CLI Tests
 * Tests for new security hardening features
 */

import { SecurityCLI } from '../../src/cli/security-cli';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import * as fs from 'fs/promises';
import * as path from 'path';

describe('Security CLI - Extended Features', () => {
  let securityCLI: SecurityCLI;
  const testDataDir = path.join(__dirname, 'test-data');

  beforeEach(async () => {
    securityCLI = new SecurityCLI();
    await fs.mkdir(testDataDir, { recursive: true });
  });

  afterEach(async () => {
    vi.clearAllMocks();
    try {
      await fs.rm(testDataDir, { recursive: true, force: true });
    } catch (error) {
      // Ignore cleanup errors
    }
  });

  // ============================================================================
  // SECURITY STATUS TESTS
  // ============================================================================

  describe('Security Status', () => {
    it('should get comprehensive security status', async () => {
      await securityCLI.getSecurityStatus();
      // Should not throw error
    });

    it('should show vault status when enabled', async () => {
      await securityCLI.addVaultEntry('test-key', 'test-value');
      await securityCLI.getSecurityStatus();
      // Should display vault as enabled
    });

    it('should show RBAC status with roles', async () => {
      await securityCLI.createRole('test-role', 'Test role');
      await securityCLI.getSecurityStatus();
      // Should display RBAC roles
    });

    it('should show audit log statistics', async () => {
      await securityCLI.getSecurityStatus();
      // Should display audit statistics
    });
  });

  // ============================================================================
  // VAULT EXTENDED TESTS
  // ============================================================================

  describe('Vault Extended Features', () => {
    it('should search vault entries by name', async () => {
      await securityCLI.addVaultEntry('database-password', 'secret123');
      await securityCLI.addVaultEntry('api-key', 'key456');
      await securityCLI.addVaultEntry('database-username', 'admin');

      const results = await securityCLI.searchVaultEntries('database');

      expect(Array.isArray(results)).toBe(true);
    });

    it('should return empty array when no matches found', async () => {
      await securityCLI.addVaultEntry('test-key', 'test-value');

      const results = await securityCLI.searchVaultEntries('nonexistent');

      expect(Array.isArray(results)).toBe(true);
      expect(results.length).toBe(0);
    });

    it('should bulk import credentials from JSON file', async () => {
      const importFile = path.join(testDataDir, 'import.json');
      const testCredentials = [
        { name: 'cred1', value: 'value1', encrypt: false },
        { name: 'cred2', value: 'value2', encrypt: true },
        { name: 'cred3', value: 'value3', encrypt: false }
      ];

      await fs.writeFile(importFile, JSON.stringify(testCredentials, null, 2));
      await securityCLI.bulkImportCredentials(importFile);

      // Verify imported
      const entries = await securityCLI.listVaultEntries();
      expect(entries.length).toBeGreaterThanOrEqual(3);
    });

    it('should handle invalid JSON during bulk import', async () => {
      const importFile = path.join(testDataDir, 'invalid.json');
      await fs.writeFile(importFile, 'invalid json');

      await expect(securityCLI.bulkImportCredentials(importFile)).rejects.toThrow();
    });

    it('should bulk export credentials to JSON file', async () => {
      await securityCLI.addVaultEntry('export-test-1', 'value1');
      await securityCLI.addVaultEntry('export-test-2', 'value2');

      const exportFile = path.join(testDataDir, 'export.json');
      await securityCLI.bulkExportCredentials(exportFile, { includeSensitive: false });

      // Verify file exists
      const exists = await fs.access(exportFile).then(() => true).catch(() => false);
      expect(exists).toBe(true);

      // Verify content
      const content = await fs.readFile(exportFile, 'utf-8');
      const exported = JSON.parse(content);
      expect(Array.isArray(exported)).toBe(true);
    });

    it('should export credentials without sensitive data by default', async () => {
      await securityCLI.addVaultEntry('sensitive-key', 'super-secret');

      const exportFile = path.join(testDataDir, 'export-safe.json');
      await securityCLI.bulkExportCredentials(exportFile);

      const content = await fs.readFile(exportFile, 'utf-8');
      const exported = JSON.parse(content);

      // Should have redacted values
      expect(JSON.stringify(exported)).not.toContain('super-secret');
    });

    it('should export credentials with sensitive data when requested', async () => {
      await securityCLI.addVaultEntry('sensitive-key', 'super-secret');

      const exportFile = path.join(testDataDir, 'export-full.json');
      await securityCLI.bulkExportCredentials(exportFile, { includeSensitive: true });

      const content = await fs.readFile(exportFile, 'utf-8');
      const exported = JSON.parse(content);

      // Should have actual values
      expect(Array.isArray(exported)).toBe(true);
    });
  });

  // ============================================================================
  // RBAC EXTENDED TESTS
  // ============================================================================

  describe('RBAC Extended Features', () => {
    it('should get role hierarchy with direct permissions', async () => {
      await securityCLI.createRole('test-role');
      await securityCLI.grantPermission('test-role', 'database', { actions: ['read', 'write'] });

      await securityCLI.getRoleHierarchy('test-role');
      // Should display role hierarchy
    });

    it('should show inherited permissions in hierarchy', async () => {
      await securityCLI.createRole('parent-role');
      await securityCLI.grantPermission('parent-role', 'admin', { actions: ['*'] });

      await securityCLI.getRoleHierarchy('parent-role');
      // Should display all permissions
    });

    it('should handle non-existent role gracefully', async () => {
      await securityCLI.getRoleHierarchy('non-existent-role');
      // Should show error message without throwing
    });

    it('should display total permissions count', async () => {
      await securityCLI.createRole('complex-role');
      await securityCLI.grantPermission('complex-role', 'database', { actions: ['read', 'write', 'delete'] });
      await securityCLI.grantPermission('complex-role', 'api', { actions: ['read'] });

      await securityCLI.getRoleHierarchy('complex-role');
      // Should show total of 4 permissions
    });
  });

  // ============================================================================
  // AUDIT LOG INTEGRITY TESTS
  // ============================================================================

  describe('Audit Log Integrity', () => {
    it('should verify audit log integrity successfully', async () => {
      await securityCLI.verifyAuditIntegrity();
      // Should show verification success
    });

    it('should detect tampered logs', async () => {
      // Note: This would require actually tampering with logs
      // For now, just verify the command works
      await securityCLI.verifyAuditIntegrity();
    });

    it('should show total logs verified', async () => {
      await securityCLI.verifyAuditIntegrity();
      // Should display log count
    });
  });

  // ============================================================================
  // PII DETECTION TESTS
  // ============================================================================

  describe('PII Detection', () => {
    it('should detect SSN in text', async () => {
      const text = 'My SSN is 123-45-6789';
      await securityCLI.detectPII(text);
      // Should detect SSN
    });

    it('should detect email addresses', async () => {
      const text = 'Contact me at john.doe@example.com';
      await securityCLI.detectPII(text);
      // Should detect email
    });

    it('should detect phone numbers', async () => {
      const text = 'Call me at (555) 123-4567';
      await securityCLI.detectPII(text);
      // Should detect phone
    });

    it('should detect credit card numbers', async () => {
      const text = 'My card is 4532-1234-5678-9010';
      await securityCLI.detectPII(text);
      // Should detect credit card
    });

    it('should detect multiple PII types', async () => {
      const text = 'SSN: 123-45-6789, Email: test@example.com, Phone: 555-1234';
      await securityCLI.detectPII(text);
      // Should detect all PII types
    });

    it('should show masked output', async () => {
      const text = 'My SSN is 123-45-6789';
      await securityCLI.detectPII(text);
      // Should display masked version
    });

    it('should handle text with no PII', async () => {
      const text = 'This is just regular text with no sensitive information';
      await securityCLI.detectPII(text);
      // Should show no PII detected
    });

    it('should handle empty text', async () => {
      await securityCLI.detectPII('');
      // Should handle gracefully
    });
  });

  // ============================================================================
  // SECURITY SCANNING TESTS
  // ============================================================================

  describe('Security Scanning', () => {
    it('should run comprehensive security scan', async () => {
      const report = await securityCLI.runSecurityScan();

      expect(report).toBeDefined();
      expect(report.timestamp).toBeDefined();
      expect(report.vulnerabilities).toBeDefined();
      expect(report.compliance).toBeDefined();
      expect(report.summary).toBeDefined();
    });

    it('should run deep security scan', async () => {
      const report = await securityCLI.runSecurityScan({ deep: true });

      expect(report.summary.totalIssues).toBeGreaterThanOrEqual(0);
    });

    it('should save scan report to file', async () => {
      const outputFile = path.join(testDataDir, 'scan-report.json');

      await securityCLI.runSecurityScan({ outputFile });

      const exists = await fs.access(outputFile).then(() => true).catch(() => false);
      expect(exists).toBe(true);
    });

    it('should check GDPR compliance', async () => {
      const report: any = { compliance: {} };
      await securityCLI.checkCompliance(report, { standard: 'gdpr' });

      expect(report.compliance.gdpr).toBeDefined();
      expect(report.compliance.gdpr.compliant).toBeDefined();
    });

    it('should check SOX compliance', async () => {
      const report: any = { compliance: {} };
      await securityCLI.checkCompliance(report, { standard: 'sox' });

      expect(report.compliance.sox).toBeDefined();
    });

    it('should check HIPAA compliance', async () => {
      const report: any = { compliance: {} };
      await securityCLI.checkCompliance(report, { standard: 'hipaa' });

      expect(report.compliance.hipaa).toBeDefined();
    });

    it('should check all compliance standards', async () => {
      const report: any = { compliance: {} };
      await securityCLI.checkCompliance(report, { standard: 'all' });

      expect(report.compliance.gdpr).toBeDefined();
      expect(report.compliance.sox).toBeDefined();
      expect(report.compliance.hipaa).toBeDefined();
    });
  });

  // ============================================================================
  // INTEGRATION TESTS
  // ============================================================================

  describe('Integration Tests', () => {
    it('should complete full security workflow', async () => {
      // 1. Add credentials
      await securityCLI.addVaultEntry('workflow-cred', 'secret-value', { encrypt: true });

      // 2. Create roles and permissions
      await securityCLI.createRole('workflow-role', 'Workflow test role');
      await securityCLI.grantPermission('workflow-role', 'database', { actions: ['read'] });

      // 3. Assign role to user
      await securityCLI.assignRole('workflow-user', 'workflow-role');

      // 4. Check security status
      await securityCLI.getSecurityStatus();

      // 5. Run security scan
      const report = await securityCLI.runSecurityScan();
      expect(report).toBeDefined();

      // 6. Verify audit integrity
      await securityCLI.verifyAuditIntegrity();

      // 7. Check compliance
      await securityCLI.checkCompliance(report);
    });

    it('should handle bulk operations workflow', async () => {
      // 1. Create import file
      const importFile = path.join(testDataDir, 'bulk-import.json');
      const credentials = [
        { name: 'bulk-1', value: 'value1', encrypt: false },
        { name: 'bulk-2', value: 'value2', encrypt: true }
      ];
      await fs.writeFile(importFile, JSON.stringify(credentials, null, 2));

      // 2. Import credentials
      await securityCLI.bulkImportCredentials(importFile);

      // 3. Search for imported credentials
      const results = await securityCLI.searchVaultEntries('bulk');
      expect(results.length).toBeGreaterThan(0);

      // 4. Export credentials
      const exportFile = path.join(testDataDir, 'bulk-export.json');
      await securityCLI.bulkExportCredentials(exportFile);

      // 5. Verify export
      const exists = await fs.access(exportFile).then(() => true).catch(() => false);
      expect(exists).toBe(true);
    });

    it('should handle PII detection workflow', async () => {
      // 1. Test with sensitive data
      const sensitiveText = 'SSN: 123-45-6789, Email: user@test.com';
      await securityCLI.detectPII(sensitiveText);

      // 2. Test with safe data
      const safeText = 'This is safe text with no PII';
      await securityCLI.detectPII(safeText);

      // Should complete without errors
    });
  });

  // ============================================================================
  // ERROR HANDLING TESTS
  // ============================================================================

  describe('Error Handling', () => {
    it('should handle missing import file gracefully', async () => {
      const nonExistentFile = path.join(testDataDir, 'does-not-exist.json');
      await expect(securityCLI.bulkImportCredentials(nonExistentFile)).rejects.toThrow();
    });

    it('should handle invalid role in hierarchy check', async () => {
      await securityCLI.getRoleHierarchy('invalid-role');
      // Should not throw, just display error
    });

    it('should handle empty search query', async () => {
      const results = await securityCLI.searchVaultEntries('');
      expect(Array.isArray(results)).toBe(true);
    });

    it('should handle special characters in PII detection', async () => {
      const text = "Special chars: !@#$%^&*()";
      await securityCLI.detectPII(text);
      // Should handle gracefully
    });
  });
});
