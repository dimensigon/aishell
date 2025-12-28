# SSO Integration Guide

Enterprise Single Sign-On (SSO) integration for AI-Shell with support for multiple providers.

## Table of Contents

- [Overview](#overview)
- [Supported Providers](#supported-providers)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Provider Configuration](#provider-configuration)
- [Authentication](#authentication)
- [Role Mapping](#role-mapping)
- [Advanced Configuration](#advanced-configuration)
- [Security Best Practices](#security-best-practices)
- [Troubleshooting](#troubleshooting)
- [API Reference](#api-reference)

## Overview

AI-Shell SSO integration provides enterprise-grade authentication with support for:

- **OAuth 2.0 / OpenID Connect (OIDC)** - Modern authentication standard
- **SAML 2.0** - Enterprise federation (future release)
- **PKCE (Proof Key for Code Exchange)** - Enhanced security
- **Automatic Token Refresh** - Seamless session management
- **Role-Based Access Control** - Map SSO roles to AI-Shell permissions
- **Multi-Factor Authentication** - Support for MFA-enabled providers
- **Session Management** - Secure, persistent sessions

### Supported Providers

1. **Okta** - Enterprise identity management
2. **Auth0** - Universal authentication platform
3. **Azure AD** - Microsoft identity platform
4. **Google Workspace** - Google Cloud identity
5. **Generic OIDC** - Any OpenID Connect provider

## Installation

SSO functionality is built into AI-Shell. No additional installation required.

### Prerequisites

- Node.js >= 18.0.0
- AI-Shell installed
- SSO provider account (Okta, Auth0, Azure AD, etc.)

## Quick Start

### 1. Configure SSO Provider

```bash
# Using a template (recommended)
ai-shell sso configure okta-prod --template okta

# Manual configuration
ai-shell sso configure my-provider
```

### 2. Login

```bash
ai-shell sso login okta-prod
```

### 3. Check Status

```bash
ai-shell sso status
```

### 4. Logout

```bash
ai-shell sso logout
```

## Provider Configuration

### Okta Configuration

#### Step 1: Create Application in Okta

1. Log in to Okta Admin Console
2. Navigate to **Applications** → **Applications**
3. Click **Create App Integration**
4. Select **OIDC - OpenID Connect**
5. Choose **Native Application**
6. Configure:
   - **Application name**: AI-Shell
   - **Grant type**: Authorization Code + Refresh Token
   - **Sign-in redirect URIs**: `http://localhost:8888/callback`
   - **Assignments**: Assign users/groups

#### Step 2: Configure in AI-Shell

```bash
ai-shell sso configure okta-prod --template okta
```

When prompted, provide:
- **Okta Domain**: `https://dev-12345.okta.com`
- **Client ID**: From your Okta application
- **Client Secret**: From your Okta application (optional for PKCE)

#### Example Configuration

```json
{
  "name": "okta-prod",
  "type": "oidc",
  "enabled": true,
  "issuer": "https://dev-12345.okta.com",
  "clientId": "0oa1234567890abcdef",
  "clientSecret": "***",
  "redirectUri": "http://localhost:8888/callback",
  "scopes": ["openid", "profile", "email"],
  "usePKCE": true,
  "roleClaimPath": "groups"
}
```

### Auth0 Configuration

#### Step 1: Create Application in Auth0

1. Log in to Auth0 Dashboard
2. Navigate to **Applications** → **Applications**
3. Click **Create Application**
4. Select **Native**
5. Configure:
   - **Name**: AI-Shell
   - **Allowed Callback URLs**: `http://localhost:8888/callback`
   - **Allowed Logout URLs**: `http://localhost:8888/logout`
   - **Grant Types**: Authorization Code + Refresh Token

#### Step 2: Configure in AI-Shell

```bash
ai-shell sso configure auth0-prod --template auth0
```

When prompted, provide:
- **Auth0 Domain**: `https://dev-12345.auth0.com`
- **Client ID**: From your Auth0 application
- **Client Secret**: From your Auth0 application
- **API Audience** (optional): For API access

#### Example Configuration

```json
{
  "name": "auth0-prod",
  "type": "oidc",
  "enabled": true,
  "issuer": "https://dev-12345.auth0.com",
  "clientId": "abc123xyz789",
  "clientSecret": "***",
  "audience": "https://api.example.com",
  "redirectUri": "http://localhost:8888/callback",
  "scopes": ["openid", "profile", "email"],
  "usePKCE": true,
  "roleClaimPath": "https://auth0.com/roles"
}
```

### Azure AD Configuration

#### Step 1: Register Application in Azure Portal

1. Log in to Azure Portal
2. Navigate to **Azure Active Directory** → **App registrations**
3. Click **New registration**
4. Configure:
   - **Name**: AI-Shell
   - **Supported account types**: Your organization only
   - **Redirect URI**: Public client/native → `http://localhost:8888/callback`
5. After creation:
   - Note the **Application (client) ID**
   - Note the **Directory (tenant) ID**
   - Create a **Client Secret** under Certificates & secrets

#### Step 2: Configure API Permissions

1. Navigate to **API permissions**
2. Add permissions:
   - Microsoft Graph → Delegated → openid, profile, email, User.Read
3. Grant admin consent

#### Step 3: Configure in AI-Shell

```bash
ai-shell sso configure azure-prod --template azure-ad
```

When prompted, provide:
- **Tenant ID**: Your Azure AD tenant ID
- **Application ID**: Your application (client) ID
- **Client Secret**: From Azure portal

#### Example Configuration

```json
{
  "name": "azure-prod",
  "type": "oidc",
  "enabled": true,
  "issuer": "https://login.microsoftonline.com/{tenant-id}/v2.0",
  "clientId": "12345678-1234-1234-1234-123456789abc",
  "clientSecret": "***",
  "redirectUri": "http://localhost:8888/callback",
  "scopes": ["openid", "profile", "email"],
  "usePKCE": true,
  "roleClaimPath": "roles"
}
```

### Google Workspace Configuration

#### Step 1: Create OAuth Client in Google Cloud

1. Log in to Google Cloud Console
2. Navigate to **APIs & Services** → **Credentials**
3. Click **Create Credentials** → **OAuth client ID**
4. Configure:
   - **Application type**: Desktop app
   - **Name**: AI-Shell
5. Note the **Client ID** and **Client secret**

#### Step 2: Configure OAuth Consent Screen

1. Navigate to **OAuth consent screen**
2. Configure:
   - **User Type**: Internal (for Workspace) or External
   - **Scopes**: openid, profile, email

#### Step 3: Configure in AI-Shell

```bash
ai-shell sso configure google-prod --template google
```

When prompted, provide:
- **Client ID**: From Google Cloud Console
- **Client Secret**: From Google Cloud Console

#### Example Configuration

```json
{
  "name": "google-prod",
  "type": "oidc",
  "enabled": true,
  "issuer": "https://accounts.google.com",
  "clientId": "123456789-abc123.apps.googleusercontent.com",
  "clientSecret": "***",
  "redirectUri": "http://localhost:8888/callback",
  "scopes": ["openid", "profile", "email"],
  "usePKCE": true,
  "roleClaimPath": "groups"
}
```

### Generic OIDC Configuration

For any OpenID Connect compliant provider:

```bash
ai-shell sso configure custom-provider --template generic
```

When prompted, provide:
- **Issuer URL**: Your OIDC provider's issuer URL
- **Client ID**: Your client ID
- **Client Secret**: Your client secret
- **Role Claim Path**: Where roles are stored in the JWT token

## Authentication

### Login

#### Basic Login

```bash
ai-shell sso login
```

If multiple providers are configured, you'll be prompted to select one.

#### Login with Specific Provider

```bash
ai-shell sso login okta-prod
```

#### Login Flow

1. Command starts a local callback server on port 8888
2. Browser opens with authorization URL
3. User authenticates with SSO provider
4. Provider redirects back to callback server
5. AI-Shell exchanges authorization code for tokens
6. Session is created and saved

### Check Status

View active SSO sessions:

```bash
ai-shell sso status
```

Output:
```
🔐 SSO Status

→ okta-prod
   User: john.doe@example.com
   Roles: admin, developer
   Status: Active
   Expires: 45 minutes
   Session ID: abc123xyz789
```

### Refresh Token

Manually refresh access token:

```bash
ai-shell sso refresh-token
```

Tokens are automatically refreshed when they expire within 5 minutes.

### Logout

End SSO session and revoke tokens:

```bash
ai-shell sso logout
```

This will:
1. Revoke tokens with the SSO provider
2. Clear local session
3. Stop callback server

## Role Mapping

Map SSO roles/groups to AI-Shell permissions.

### Add Role Mapping

```bash
ai-shell sso map-roles
```

Interactive prompts:
1. Select action: **Add role mapping**
2. Enter SSO role name (e.g., `okta-admins`)
3. Select AI-Shell role: `admin`, `developer`, `user`, `readonly`
4. Enter description (optional)

### Available AI-Shell Roles

- **admin** - Full system access
- **developer** - Development and deployment access
- **user** - Standard user access
- **readonly** - Read-only access

### List Role Mappings

```bash
ai-shell sso map-roles
```

Then select: **Exit** to view current mappings.

### Example Role Mappings

```json
[
  {
    "ssoRole": "okta-admins",
    "aiShellRole": "admin",
    "description": "Okta admin group"
  },
  {
    "ssoRole": "developers",
    "aiShellRole": "developer",
    "description": "Development team"
  },
  {
    "ssoRole": "users",
    "aiShellRole": "user",
    "description": "Standard users"
  }
]
```

### Role Claim Paths

Different providers store roles in different places:

| Provider | Role Claim Path | Example |
|----------|----------------|---------|
| Okta | `groups` | User's Okta groups |
| Auth0 | `https://auth0.com/roles` | Custom namespace |
| Azure AD | `roles` | App roles |
| Google | `groups` | Google Groups |

## Advanced Configuration

### Custom Callback Port

Change the callback server port:

```bash
# Edit ~/.aishell/sso/providers.json
{
  "callbackPort": 3000
}
```

Update redirect URIs in your SSO provider.

### Session Timeout

Configure session timeout (milliseconds):

```bash
# Edit ~/.aishell/sso/providers.json
{
  "sessionTimeout": 86400000  # 24 hours
}
```

### Token Refresh Threshold

Configure when to auto-refresh tokens (milliseconds):

```bash
# Edit ~/.aishell/sso/providers.json
{
  "tokenRefreshThreshold": 300000  # 5 minutes
}
```

### Custom Parameters

Add custom OAuth parameters:

```json
{
  "name": "custom-provider",
  "customParams": {
    "prompt": "consent",
    "access_type": "offline",
    "include_granted_scopes": "true"
  }
}
```

### Multiple Environments

Configure different providers for different environments:

```bash
# Development
ai-shell sso configure okta-dev --template okta

# Staging
ai-shell sso configure okta-staging --template okta

# Production
ai-shell sso configure okta-prod --template okta
```

## Security Best Practices

### 1. Use PKCE

Always enable PKCE for enhanced security:

```json
{
  "usePKCE": true
}
```

### 2. Store Secrets Securely

- Use AI-Shell's encrypted vault for client secrets
- Never commit secrets to version control
- Rotate secrets regularly

### 3. Limit Scopes

Only request necessary scopes:

```json
{
  "scopes": ["openid", "profile", "email"]
}
```

### 4. Session Management

- Configure appropriate session timeouts
- Implement automatic logout on inactivity
- Revoke tokens on logout

### 5. Token Storage

- Tokens are encrypted at rest
- Stored in `~/.aishell/sso/`
- Protected by file system permissions

### 6. Network Security

#### Development

- Use `http://localhost:8888/callback` for local development
- Callback server only accepts local connections

#### Production

- Use HTTPS for callback URLs
- Configure proper TLS certificates
- Use reverse proxy for additional security

### 7. Role-Based Access Control

- Map SSO roles to least-privilege AI-Shell roles
- Regular audit role mappings
- Document role assignments

### 8. Audit Logging

All SSO operations are logged:

```bash
# View SSO audit logs
ai-shell security audit-log --action sso_login
```

### 9. Multi-Factor Authentication

- Enable MFA in your SSO provider
- AI-Shell automatically supports provider MFA
- MFA challenges handled by provider

### 10. Token Revocation

Always revoke tokens on logout:

```bash
ai-shell sso logout
```

## Troubleshooting

### Common Issues

#### 1. "Provider not found"

**Problem**: Attempting to use unconfigured provider.

**Solution**:
```bash
# List configured providers
ai-shell sso list-providers

# Configure missing provider
ai-shell sso configure <provider-name>
```

#### 2. "Authorization failed"

**Problem**: SSO provider rejected authentication.

**Solutions**:
- Verify credentials are correct
- Check provider configuration (issuer, client ID)
- Ensure redirect URI matches provider settings
- Check user has access to application

#### 3. "Token expired"

**Problem**: Session token has expired.

**Solution**:
```bash
# Refresh token
ai-shell sso refresh-token

# Or re-login
ai-shell sso login
```

#### 4. "Callback timeout"

**Problem**: Callback server didn't receive response.

**Solutions**:
- Check firewall allows localhost connections
- Verify callback port (default 8888) is available
- Check browser popup blockers
- Verify redirect URI in provider matches configured URI

#### 5. "Invalid JWT"

**Problem**: Token format is invalid.

**Solutions**:
- Check issuer URL is correct
- Verify provider is OIDC compliant
- Check token hasn't been tampered with

#### 6. "No roles mapped"

**Problem**: User authenticated but has no permissions.

**Solutions**:
```bash
# Add role mapping
ai-shell sso map-roles

# Check role claim path
ai-shell sso show-config <provider>
```

### Debug Mode

Enable debug logging:

```bash
export LOG_LEVEL=debug
ai-shell sso login
```

### Check Configuration

View current provider configuration:

```bash
ai-shell sso show-config <provider-name>
```

### Test Connection

Test provider connectivity:

```bash
# Attempt login
ai-shell sso login <provider>

# Check status
ai-shell sso status
```

### Logs Location

SSO logs are stored in:
- Configuration: `~/.aishell/sso/providers.json`
- Sessions: `~/.aishell/sso/sessions.json`
- Role mappings: `~/.aishell/sso/role-mappings.json`
- Application logs: `~/.aishell/logs/`

## API Reference

### CLI Commands

#### configure

Configure SSO provider.

```bash
ai-shell sso configure <provider-name> [--template <template>]
```

**Arguments**:
- `provider-name` - Unique provider identifier

**Options**:
- `--template` - Use provider template (okta, auth0, azure-ad, google, generic)

**Example**:
```bash
ai-shell sso configure okta-prod --template okta
```

#### login

Authenticate with SSO provider.

```bash
ai-shell sso login [provider-name]
```

**Arguments**:
- `provider-name` (optional) - Provider to use for login

**Example**:
```bash
ai-shell sso login okta-prod
```

#### logout

End SSO session.

```bash
ai-shell sso logout
```

#### status

Show current SSO status.

```bash
ai-shell sso status
```

#### refresh-token

Refresh access token.

```bash
ai-shell sso refresh-token [session-id]
```

**Arguments**:
- `session-id` (optional) - Specific session to refresh

#### map-roles

Configure role mappings.

```bash
ai-shell sso map-roles
```

Interactive prompts guide role mapping configuration.

#### list-providers

List all configured providers.

```bash
ai-shell sso list-providers
```

#### show-config

Show provider configuration.

```bash
ai-shell sso show-config <provider-name>
```

#### remove-provider

Remove SSO provider.

```bash
ai-shell sso remove-provider <provider-name>
```

### Programmatic API

#### SSOManager

```typescript
import { SSOManager } from 'ai-shell/cli/sso-manager';

const ssoManager = new SSOManager();
await ssoManager.initialize();

// Configure provider
await ssoManager.configureProvider('okta', {
  type: 'oidc',
  enabled: true,
  issuer: 'https://dev-12345.okta.com',
  clientId: 'client-id',
  clientSecret: 'client-secret'
});

// Login
const session = await ssoManager.login('okta');

// Get current session
const current = ssoManager.getCurrentSession();

// Refresh token
const refreshed = await ssoManager.refreshToken(session.sessionId);

// Logout
await ssoManager.logout(session.sessionId);
```

#### Events

SSOManager emits events for monitoring:

```typescript
ssoManager.on('provider-configured', (name) => {
  console.log(`Provider ${name} configured`);
});

ssoManager.on('session-created', (session) => {
  console.log(`Session created: ${session.sessionId}`);
});

ssoManager.on('token-refreshed', (session) => {
  console.log(`Token refreshed: ${session.sessionId}`);
});

ssoManager.on('session-ended', (session) => {
  console.log(`Session ended: ${session.sessionId}`);
});
```

## Examples

### Example 1: Okta Integration

Complete Okta SSO setup:

```bash
# 1. Configure Okta
ai-shell sso configure okta-prod --template okta
# Enter: https://dev-12345.okta.com
# Enter: client-id
# Enter: client-secret

# 2. Add role mappings
ai-shell sso map-roles
# Add: okta-admins → admin
# Add: okta-developers → developer
# Add: okta-users → user

# 3. Login
ai-shell sso login okta-prod
# Browser opens → Authenticate → Redirected back

# 4. Verify
ai-shell sso status
```

### Example 2: Multi-Provider Setup

Configure multiple providers:

```bash
# Configure Okta for internal users
ai-shell sso configure okta-internal --template okta

# Configure Auth0 for external users
ai-shell sso configure auth0-external --template auth0

# Configure Azure AD for partners
ai-shell sso configure azure-partners --template azure-ad

# List all providers
ai-shell sso list-providers

# Login with specific provider
ai-shell sso login auth0-external
```

### Example 3: Role Mapping

Complete role mapping setup:

```bash
# Configure provider
ai-shell sso configure okta-prod --template okta

# Set role claim path to "groups"
# (configured during provider setup)

# Map roles
ai-shell sso map-roles

# Mappings:
# engineering-admins → admin
# engineering-devs → developer
# engineering-qa → user
# external-contractors → readonly

# Test
ai-shell sso login okta-prod
ai-shell sso status
# Roles shown based on mappings
```

## Support

For issues or questions:

1. Check [Troubleshooting](#troubleshooting) section
2. Enable debug logging
3. Review logs in `~/.aishell/logs/`
4. Contact support with:
   - Provider type
   - Error messages
   - Debug logs (remove sensitive data)

## Related Documentation

- [Security CLI](./security-cli.md)
- [RBAC Configuration](./rbac.md)
- [Audit Logging](./audit-logging.md)
- [Vault Management](./vault.md)
