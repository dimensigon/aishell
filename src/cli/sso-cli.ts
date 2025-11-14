/**
 * SSO CLI - Command-line interface for SSO management
 *
 * Commands:
 * - configure <provider> - Configure SSO provider
 * - login [provider] - Authenticate with SSO
 * - logout - End SSO session
 * - status - Show current SSO status
 * - refresh-token - Refresh access token
 * - map-roles - Configure role mappings
 *
 * @module SSOCLI
 */

import { SSOManager, SSOProviderConfig, RoleMapping } from './sso-manager';
import { createLogger } from '../core/logger';
import chalk from 'chalk';
import Table from 'cli-table3';
import inquirer from 'inquirer';

export class SSOCLI {
  private logger = createLogger('SSOCLI');
  private ssoManager: SSOManager;

  constructor() {
    this.ssoManager = new SSOManager();
  }

  /**
   * Initialize CLI
   */
  async initialize(): Promise<void> {
    await this.ssoManager.initialize();
  }

  // ============================================================================
  // CONFIGURATION COMMANDS
  // ============================================================================

  /**
   * Configure SSO provider
   */
  async configure(providerName: string, template?: string): Promise<void> {
    try {
      console.log(chalk.blue(`\n🔐 Configuring SSO Provider: ${providerName}\n`));

      let config: Partial<SSOProviderConfig>;

      if (template) {
        // Use template
        const validTemplates = ['okta', 'auth0', 'azure-ad', 'google', 'generic'];
        if (!validTemplates.includes(template)) {
          throw new Error(
            `Invalid template: ${template}. Valid templates: ${validTemplates.join(', ')}`
          );
        }

        await this.ssoManager.configureProviderTemplate(
          providerName,
          template as any
        );

        // Get additional details
        config = await this.promptProviderDetails(template as any);

      } else {
        // Manual configuration
        config = await this.promptProviderConfiguration();
      }

      // Apply configuration
      await this.ssoManager.configureProvider(providerName, config);

      console.log(chalk.green(`\n✅ Provider '${providerName}' configured successfully\n`));

      // Show configuration
      await this.showProviderConfig(providerName);

    } catch (error) {
      this.logger.error('Configure command failed', error);
      console.log(chalk.red(`\n❌ Configuration failed: ${error}\n`));
      throw error;
    }
  }

  /**
   * Prompt for provider configuration
   */
  private async promptProviderConfiguration(): Promise<Partial<SSOProviderConfig>> {
    const answers = await inquirer.prompt([
      {
        type: 'list',
        name: 'type',
        message: 'Provider type:',
        choices: [
          { name: 'OpenID Connect (OIDC)', value: 'oidc' },
          { name: 'SAML 2.0', value: 'saml' }
        ]
      },
      {
        type: 'input',
        name: 'issuer',
        message: 'Issuer URL (for OIDC):',
        when: (answers) => answers.type === 'oidc',
        validate: (input) => input.length > 0 || 'Issuer URL is required'
      },
      {
        type: 'input',
        name: 'clientId',
        message: 'Client ID:',
        validate: (input) => input.length > 0 || 'Client ID is required'
      },
      {
        type: 'password',
        name: 'clientSecret',
        message: 'Client Secret (optional):',
        mask: '*'
      },
      {
        type: 'input',
        name: 'redirectUri',
        message: 'Redirect URI (default: http://localhost:8888/callback):',
        default: 'http://localhost:8888/callback'
      },
      {
        type: 'input',
        name: 'scopes',
        message: 'Scopes (comma-separated):',
        default: 'openid,profile,email',
        filter: (input) => input.split(',').map((s: string) => s.trim())
      },
      {
        type: 'confirm',
        name: 'usePKCE',
        message: 'Use PKCE (recommended):',
        default: true
      },
      {
        type: 'input',
        name: 'roleClaimPath',
        message: 'Role claim path (e.g., "roles" or "groups"):',
        default: 'roles'
      },
      {
        type: 'confirm',
        name: 'enabled',
        message: 'Enable this provider:',
        default: true
      }
    ]);

    return answers;
  }

  /**
   * Prompt for template-specific details
   */
  private async promptProviderDetails(template: string): Promise<Partial<SSOProviderConfig>> {
    const prompts: any = {
      okta: [
        {
          type: 'input',
          name: 'issuer',
          message: 'Okta Domain (e.g., https://dev-12345.okta.com):',
          validate: (input: string) => input.includes('okta.com') || 'Enter a valid Okta domain'
        },
        {
          type: 'input',
          name: 'clientId',
          message: 'Client ID:',
          validate: (input: string) => input.length > 0 || 'Client ID is required'
        },
        {
          type: 'password',
          name: 'clientSecret',
          message: 'Client Secret (optional):',
          mask: '*'
        }
      ],
      auth0: [
        {
          type: 'input',
          name: 'issuer',
          message: 'Auth0 Domain (e.g., https://dev-12345.auth0.com):',
          validate: (input: string) => input.includes('auth0.com') || 'Enter a valid Auth0 domain'
        },
        {
          type: 'input',
          name: 'clientId',
          message: 'Client ID:',
          validate: (input: string) => input.length > 0 || 'Client ID is required'
        },
        {
          type: 'password',
          name: 'clientSecret',
          message: 'Client Secret:',
          mask: '*',
          validate: (input: string) => input.length > 0 || 'Client Secret is required'
        },
        {
          type: 'input',
          name: 'audience',
          message: 'API Audience (optional):'
        }
      ],
      'azure-ad': [
        {
          type: 'input',
          name: 'issuer',
          message: 'Azure AD Tenant ID or Domain:',
          validate: (input: string) => input.length > 0 || 'Tenant ID is required',
          filter: (input: string) =>
            input.includes('.')
              ? `https://login.microsoftonline.com/${input}/v2.0`
              : `https://login.microsoftonline.com/${input}/v2.0`
        },
        {
          type: 'input',
          name: 'clientId',
          message: 'Application (client) ID:',
          validate: (input: string) => input.length > 0 || 'Client ID is required'
        },
        {
          type: 'password',
          name: 'clientSecret',
          message: 'Client Secret:',
          mask: '*'
        }
      ],
      google: [
        {
          type: 'input',
          name: 'issuer',
          message: 'Google Workspace Domain (leave empty for accounts.google.com):',
          default: 'https://accounts.google.com',
          filter: (input: string) =>
            input.includes('google.com') ? input : 'https://accounts.google.com'
        },
        {
          type: 'input',
          name: 'clientId',
          message: 'OAuth Client ID:',
          validate: (input: string) => input.includes('.apps.googleusercontent.com') || 'Enter a valid Google Client ID'
        },
        {
          type: 'password',
          name: 'clientSecret',
          message: 'Client Secret:',
          mask: '*',
          validate: (input: string) => input.length > 0 || 'Client Secret is required'
        }
      ],
      generic: [
        {
          type: 'input',
          name: 'issuer',
          message: 'OIDC Issuer URL:',
          validate: (input: string) => input.startsWith('http') || 'Enter a valid URL'
        },
        {
          type: 'input',
          name: 'clientId',
          message: 'Client ID:',
          validate: (input: string) => input.length > 0 || 'Client ID is required'
        },
        {
          type: 'password',
          name: 'clientSecret',
          message: 'Client Secret (optional):',
          mask: '*'
        },
        {
          type: 'input',
          name: 'roleClaimPath',
          message: 'Role claim path:',
          default: 'roles'
        }
      ]
    };

    const answers = await inquirer.prompt(prompts[template] || []);
    return answers;
  }

  /**
   * Show provider configuration
   */
  async showProviderConfig(providerName: string): Promise<void> {
    const provider = this.ssoManager.getProvider(providerName);
    if (!provider) {
      console.log(chalk.yellow(`\nProvider '${providerName}' not found\n`));
      return;
    }

    console.log(chalk.blue('\n📋 Provider Configuration:\n'));

    const table = new Table({
      colWidths: [25, 50]
    });

    table.push(
      ['Provider Name', provider.name],
      ['Type', provider.type.toUpperCase()],
      ['Enabled', provider.enabled ? chalk.green('Yes') : chalk.red('No')],
      ['Issuer', provider.issuer || 'N/A'],
      ['Client ID', provider.clientId || 'N/A'],
      ['Client Secret', provider.clientSecret ? '***SET***' : 'Not set'],
      ['Redirect URI', provider.redirectUri || 'http://localhost:8888/callback'],
      ['Scopes', (provider.scopes || []).join(', ')],
      ['Use PKCE', provider.usePKCE ? 'Yes' : 'No'],
      ['Role Claim Path', provider.roleClaimPath || 'N/A']
    );

    console.log(table.toString());
    console.log('');
  }

  /**
   * List all providers
   */
  async listProviders(): Promise<void> {
    const providers = this.ssoManager.listProviders();

    if (providers.length === 0) {
      console.log(chalk.yellow('\nNo SSO providers configured\n'));
      console.log(chalk.dim('Use "ai-shell sso configure <provider>" to add a provider\n'));
      return;
    }

    console.log(chalk.blue(`\n🔐 Configured SSO Providers (${providers.length})\n`));

    const table = new Table({
      head: ['Name', 'Type', 'Status', 'Issuer'].map(h => chalk.bold(h)),
      colWidths: [20, 10, 10, 50]
    });

    providers.forEach(provider => {
      table.push([
        provider.name,
        provider.type.toUpperCase(),
        provider.enabled ? chalk.green('Enabled') : chalk.red('Disabled'),
        provider.issuer || 'N/A'
      ]);
    });

    console.log(table.toString());
    console.log('');
  }

  /**
   * Remove provider
   */
  async removeProvider(providerName: string): Promise<void> {
    try {
      const confirm = await inquirer.prompt([
        {
          type: 'confirm',
          name: 'confirmed',
          message: `Are you sure you want to remove provider '${providerName}'?`,
          default: false
        }
      ]);

      if (!confirm.confirmed) {
        console.log(chalk.yellow('\nOperation cancelled\n'));
        return;
      }

      await this.ssoManager.removeProvider(providerName);
      console.log(chalk.green(`\n✅ Provider '${providerName}' removed\n`));

    } catch (error) {
      this.logger.error('Remove provider failed', error);
      console.log(chalk.red(`\n❌ Failed to remove provider: ${error}\n`));
      throw error;
    }
  }

  // ============================================================================
  // AUTHENTICATION COMMANDS
  // ============================================================================

  /**
   * Login with SSO
   */
  async login(providerName?: string): Promise<void> {
    try {
      // If no provider specified, list available providers
      if (!providerName) {
        const providers = this.ssoManager.listProviders().filter(p => p.enabled);

        if (providers.length === 0) {
          console.log(chalk.yellow('\nNo SSO providers configured\n'));
          console.log(chalk.dim('Use "ai-shell sso configure <provider>" to add a provider\n'));
          return;
        }

        if (providers.length === 1) {
          providerName = providers[0].name;
        } else {
          const answer = await inquirer.prompt([
            {
              type: 'list',
              name: 'provider',
              message: 'Select SSO provider:',
              choices: providers.map(p => ({ name: p.name, value: p.name }))
            }
          ]);
          providerName = answer.provider;
        }
      }

      // Ensure providerName is defined
      if (!providerName) {
        throw new Error('Provider name could not be determined');
      }

      console.log(chalk.blue(`\n🔐 Logging in with ${providerName}...\n`));

      // Start login flow
      const session = await this.ssoManager.login(providerName);

      console.log(chalk.green('\n✅ Authentication successful!\n'));
      console.log(chalk.dim(`   Session ID: ${session.sessionId}`));
      console.log(chalk.dim(`   User: ${session.name || session.email || session.userId || 'Unknown'}`));
      console.log(chalk.dim(`   Roles: ${session.roles.join(', ')}`));
      console.log('');

    } catch (error) {
      this.logger.error('Login failed', error);
      console.log(chalk.red(`\n❌ Authentication failed: ${error}\n`));
      throw error;
    }
  }

  /**
   * Logout from SSO
   */
  async logout(): Promise<void> {
    try {
      const session = this.ssoManager.getCurrentSession();

      if (!session) {
        console.log(chalk.yellow('\nNo active SSO session\n'));
        return;
      }

      const confirm = await inquirer.prompt([
        {
          type: 'confirm',
          name: 'confirmed',
          message: 'Are you sure you want to logout?',
          default: true
        }
      ]);

      if (!confirm.confirmed) {
        console.log(chalk.yellow('\nLogout cancelled\n'));
        return;
      }

      await this.ssoManager.logout();

      console.log(chalk.green('\n✅ Logged out successfully\n'));

    } catch (error) {
      this.logger.error('Logout failed', error);
      console.log(chalk.red(`\n❌ Logout failed: ${error}\n`));
      throw error;
    }
  }

  /**
   * Show SSO status
   */
  async status(): Promise<void> {
    try {
      const sessions = this.ssoManager.listSessions();
      const currentSession = this.ssoManager.getCurrentSession();

      if (sessions.length === 0) {
        console.log(chalk.yellow('\n⚠️  No active SSO sessions\n'));
        return;
      }

      console.log(chalk.blue(`\n🔐 SSO Status\n`));

      sessions.forEach(session => {
        const isCurrent = currentSession?.sessionId === session.sessionId;
        const expiresIn = session.token.expiresAt - Date.now();
        const expiresInMinutes = Math.floor(expiresIn / 60000);

        console.log(chalk.bold(isCurrent ? '→ ' : '  ') + session.provider);
        console.log(`   User: ${session.name || session.email || session.userId}`);
        console.log(`   Roles: ${session.roles.join(', ')}`);
        console.log(`   Status: ${expiresIn > 0 ? chalk.green('Active') : chalk.red('Expired')}`);
        console.log(`   Expires: ${expiresInMinutes > 0 ? `${expiresInMinutes} minutes` : 'Expired'}`);
        console.log(`   Session ID: ${session.sessionId}`);
        console.log('');
      });

    } catch (error) {
      this.logger.error('Status command failed', error);
      console.log(chalk.red(`\n❌ Failed to get status: ${error}\n`));
      throw error;
    }
  }

  /**
   * Refresh access token
   */
  async refreshToken(sessionId?: string): Promise<void> {
    try {
      const session = sessionId
        ? this.ssoManager.getSession(sessionId)
        : this.ssoManager.getCurrentSession();

      if (!session) {
        console.log(chalk.yellow('\nNo active session found\n'));
        return;
      }

      console.log(chalk.blue('\n🔄 Refreshing token...\n'));

      const refreshedSession = await this.ssoManager.refreshToken(session.sessionId);

      const expiresIn = refreshedSession.token.expiresAt - Date.now();
      const expiresInMinutes = Math.floor(expiresIn / 60000);

      console.log(chalk.green('✅ Token refreshed successfully\n'));
      console.log(chalk.dim(`   New expiry: ${expiresInMinutes} minutes\n`));

    } catch (error) {
      this.logger.error('Token refresh failed', error);
      console.log(chalk.red(`\n❌ Token refresh failed: ${error}\n`));
      throw error;
    }
  }

  // ============================================================================
  // ROLE MAPPING COMMANDS
  // ============================================================================

  /**
   * Configure role mappings
   */
  async mapRoles(): Promise<void> {
    try {
      console.log(chalk.blue('\n🔐 Role Mapping Configuration\n'));

      const currentMappings = this.ssoManager.listRoleMappings();

      if (currentMappings.length > 0) {
        console.log(chalk.bold('Current Mappings:\n'));

        const table = new Table({
          head: ['SSO Role', 'AI-Shell Role', 'Description'].map(h => chalk.bold(h)),
          colWidths: [25, 20, 40]
        });

        currentMappings.forEach(mapping => {
          table.push([
            mapping.ssoRole,
            mapping.aiShellRole,
            mapping.description || ''
          ]);
        });

        console.log(table.toString());
        console.log('');
      }

      const answer = await inquirer.prompt([
        {
          type: 'list',
          name: 'action',
          message: 'What would you like to do?',
          choices: [
            { name: 'Add role mapping', value: 'add' },
            { name: 'Remove role mapping', value: 'remove' },
            { name: 'Exit', value: 'exit' }
          ]
        }
      ]);

      if (answer.action === 'exit') {
        return;
      }

      if (answer.action === 'add') {
        await this.addRoleMapping();
      } else if (answer.action === 'remove') {
        await this.removeRoleMapping();
      }

    } catch (error) {
      this.logger.error('Role mapping failed', error);
      console.log(chalk.red(`\n❌ Role mapping failed: ${error}\n`));
      throw error;
    }
  }

  /**
   * Add role mapping
   */
  private async addRoleMapping(): Promise<void> {
    const answers = await inquirer.prompt([
      {
        type: 'input',
        name: 'ssoRole',
        message: 'SSO Role name:',
        validate: (input) => input.length > 0 || 'Role name is required'
      },
      {
        type: 'list',
        name: 'aiShellRole',
        message: 'Map to AI-Shell role:',
        choices: ['admin', 'developer', 'user', 'readonly']
      },
      {
        type: 'input',
        name: 'description',
        message: 'Description (optional):'
      }
    ]);

    await this.ssoManager.addRoleMapping(answers);

    console.log(chalk.green('\n✅ Role mapping added successfully\n'));
  }

  /**
   * Remove role mapping
   */
  private async removeRoleMapping(): Promise<void> {
    const mappings = this.ssoManager.listRoleMappings();

    if (mappings.length === 0) {
      console.log(chalk.yellow('\nNo role mappings configured\n'));
      return;
    }

    const answer = await inquirer.prompt([
      {
        type: 'list',
        name: 'ssoRole',
        message: 'Select role mapping to remove:',
        choices: mappings.map(m => ({
          name: `${m.ssoRole} → ${m.aiShellRole}`,
          value: m.ssoRole
        }))
      }
    ]);

    await this.ssoManager.removeRoleMapping(answer.ssoRole);

    console.log(chalk.green('\n✅ Role mapping removed\n'));
  }

  /**
   * List role mappings
   */
  async listRoleMappings(): Promise<void> {
    const mappings = this.ssoManager.listRoleMappings();

    if (mappings.length === 0) {
      console.log(chalk.yellow('\nNo role mappings configured\n'));
      console.log(chalk.dim('Use "ai-shell sso map-roles" to configure role mappings\n'));
      return;
    }

    console.log(chalk.blue(`\n🔐 Role Mappings (${mappings.length})\n`));

    const table = new Table({
      head: ['SSO Role', 'AI-Shell Role', 'Description'].map(h => chalk.bold(h)),
      colWidths: [25, 20, 45]
    });

    mappings.forEach(mapping => {
      table.push([
        mapping.ssoRole,
        mapping.aiShellRole,
        mapping.description || ''
      ]);
    });

    console.log(table.toString());
    console.log('');
  }

  /**
   * Cleanup
   */
  async cleanup(): Promise<void> {
    await this.ssoManager.stop();
  }
}

/**
 * Create and export singleton instance
 */
export function createSSOCLI(): SSOCLI {
  return new SSOCLI();
}

/**
 * Default export
 */
export default SSOCLI;
