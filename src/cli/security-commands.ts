/**
 * Security Command Helpers
 *
 * Helper functions and utilities for security CLI commands.
 * Provides convenient wrappers around SecurityCLI for command-line usage.
 *
 * @module SecurityCommands
 */

import { SecurityCLI, VaultOptions, AuditOptions, PermissionOptions } from './security-cli';
import chalk from 'chalk';
import { createLogger } from '../core/logger';

const logger = createLogger('SecurityCommands');

/**
 * Initialize security CLI instance
 */
export function createSecurityCLI(): SecurityCLI {
  return new SecurityCLI();
}

/**
 * Vault command handlers
 */
export const vaultCommands = {
  /**
   * Add credential to vault
   */
  async add(name: string, value: string, options: { encrypt?: boolean } = {}): Promise<void> {
    const cli = createSecurityCLI();
    await cli.addVaultEntry(name, value, { encrypt: options.encrypt });
  },

  /**
   * List all vault entries
   */
  async list(options: VaultOptions = {}): Promise<any[]> {
    const cli = createSecurityCLI();
    return await cli.listVaultEntries(options);
  },

  /**
   * Get specific vault entry
   */
  async get(name: string): Promise<any> {
    const cli = createSecurityCLI();
    return await cli.getVaultEntry(name);
  },

  /**
   * Delete vault entry
   */
  async delete(name: string): Promise<void> {
    const cli = createSecurityCLI();
    await cli.removeVaultEntry(name);
  },

  /**
   * Rotate vault encryption key
   */
  async rotate(): Promise<void> {
    const cli = createSecurityCLI();
    await cli.rotateVaultKey();
  }
};

/**
 * Permission command handlers
 */
export const permissionCommands = {
  /**
   * Grant permission to role for a resource
   */
  async grant(
    role: string,
    resource: string,
    options: { actions?: string[] } = {}
  ): Promise<void> {
    const cli = createSecurityCLI();
    const actions = options.actions || ['read', 'write'];

    logger.info('Granting permissions', { role, resource, actions });

    await cli.grantPermission(role, resource, { actions });
  },

  /**
   * Revoke permission from role for a resource
   */
  async revoke(role: string, resource: string): Promise<void> {
    const cli = createSecurityCLI();

    logger.info('Revoking permissions', { role, resource });

    await cli.revokePermission(role, resource);
  },

  /**
   * List permissions for user or role
   */
  async list(userOrRole?: string, options: PermissionOptions = {}): Promise<void> {
    const cli = createSecurityCLI();
    await cli.listPermissions(userOrRole, options);
  },

  /**
   * Check if user has permission
   */
  async check(user: string, resource: string, action: string): Promise<boolean> {
    const cli = createSecurityCLI();
    return await cli.checkPermission(user, resource, action);
  }
};

/**
 * Audit log command handlers
 */
export const auditCommands = {
  /**
   * Show audit log with filters
   */
  async show(options: AuditOptions = {}): Promise<any[]> {
    const cli = createSecurityCLI();
    return await cli.showAuditLog(options);
  },

  /**
   * Export audit log to file
   */
  async export(file: string, options: AuditOptions = {}): Promise<void> {
    const cli = createSecurityCLI();
    await cli.exportAuditLog(file, options);
  },

  /**
   * Show audit statistics
   */
  async stats(): Promise<void> {
    const cli = createSecurityCLI();
    await cli.auditStats();
  },

  /**
   * Search audit logs
   */
  async search(query: string): Promise<any[]> {
    const cli = createSecurityCLI();
    return await cli.searchAuditLog(query);
  },

  /**
   * Clear old audit logs
   */
  async clear(beforeDate: Date): Promise<void> {
    const cli = createSecurityCLI();
    await cli.clearAuditLog(beforeDate);
  }
};

/**
 * Role command handlers
 */
export const roleCommands = {
  /**
   * Create new role
   */
  async create(name: string, description?: string): Promise<void> {
    const cli = createSecurityCLI();
    await cli.createRole(name, description);
  },

  /**
   * Delete role
   */
  async delete(name: string): Promise<void> {
    const cli = createSecurityCLI();
    await cli.deleteRole(name);
  },

  /**
   * Assign role to user
   */
  async assign(user: string, role: string): Promise<void> {
    const cli = createSecurityCLI();
    await cli.assignRole(user, role);
  },

  /**
   * Unassign role from user
   */
  async unassign(user: string, role: string): Promise<void> {
    const cli = createSecurityCLI();
    await cli.unassignRole(user, role);
  }
};

/**
 * Encryption command handlers
 */
export const encryptionCommands = {
  /**
   * Encrypt a value
   */
  async encrypt(value: string): Promise<string> {
    const cli = createSecurityCLI();
    return await cli.encryptValue(value);
  },

  /**
   * Decrypt a value
   */
  async decrypt(encryptedValue: string): Promise<string> {
    const cli = createSecurityCLI();
    return await cli.decryptValue(encryptedValue);
  }
};

/**
 * Security status and monitoring commands
 */
export const securityCommands = {
  /**
   * Get comprehensive security status
   */
  async status(): Promise<void> {
    const cli = createSecurityCLI();
    await cli.getSecurityStatus();
  },

  /**
   * Run security scan
   */
  async scan(options: { deep?: boolean; outputFile?: string } = {}): Promise<any> {
    const cli = createSecurityCLI();
    return await cli.runSecurityScan(options);
  },

  /**
   * List known vulnerabilities
   */
  async vulnerabilities(): Promise<void> {
    const cli = createSecurityCLI();
    await cli.listVulnerabilities();
  },

  /**
   * Check compliance
   */
  async compliance(standard?: 'gdpr' | 'sox' | 'hipaa' | 'all'): Promise<void> {
    const cli = createSecurityCLI();
    const report: any = { compliance: {} };
    await cli.checkCompliance(report, { standard: standard || 'all' });
  },

  /**
   * Verify audit log integrity
   */
  async verifyIntegrity(): Promise<void> {
    const cli = createSecurityCLI();
    await cli.verifyAuditIntegrity();
  },

  /**
   * Detect PII in text
   */
  async detectPII(text: string): Promise<void> {
    const cli = createSecurityCLI();
    await cli.detectPII(text);
  }
};

/**
 * Extended vault commands
 */
export const vaultExtendedCommands = {
  ...vaultCommands,

  /**
   * Search vault entries
   */
  async search(query: string): Promise<any[]> {
    const cli = createSecurityCLI();
    return await cli.searchVaultEntries(query);
  },

  /**
   * Bulk import credentials
   */
  async import(filePath: string): Promise<void> {
    const cli = createSecurityCLI();
    await cli.bulkImportCredentials(filePath);
  },

  /**
   * Bulk export credentials
   */
  async export(filePath: string, options: { includeSensitive?: boolean } = {}): Promise<void> {
    const cli = createSecurityCLI();
    await cli.bulkExportCredentials(filePath, options);
  }
};

/**
 * Extended role commands
 */
export const roleExtendedCommands = {
  ...roleCommands,

  /**
   * Get role hierarchy
   */
  async hierarchy(roleName: string): Promise<void> {
    const cli = createSecurityCLI();
    await cli.getRoleHierarchy(roleName);
  }
};

/**
 * Default export - all command handlers
 */
export default {
  vault: vaultExtendedCommands,
  permissions: permissionCommands,
  audit: auditCommands,
  roles: roleExtendedCommands,
  encryption: encryptionCommands,
  security: securityCommands
};
