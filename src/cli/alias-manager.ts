import { createLogger } from '../core/logger';
import * as fs from 'fs/promises';
import * as path from 'path';
import * as yaml from 'js-yaml';

export interface AliasParameter {
  name: string;
  type: 'string' | 'number' | 'date' | 'boolean';
  required: boolean;
  default?: any;
  description?: string;
}

export interface Alias {
  name: string;
  query: string;
  description?: string;
  parameters?: AliasParameter[];
  createdAt: Date;
  lastUsed?: Date;
  usageCount: number;
  tags?: string[];
}

export interface AddAliasOptions {
  description?: string;
  parameters?: string;
  tags?: string[];
}

export interface RunAliasOptions {
  explain?: boolean;
  dryRun?: boolean;
  format?: 'table' | 'json' | 'csv';
}

export interface ListAliasOptions {
  verbose?: boolean;
  format?: 'table' | 'json' | 'yaml';
  tags?: string[];
}

export interface AliasTemplate {
  name: string;
  description: string;
  query: string;
  parameters?: AliasParameter[];
  tags?: string[];
}

export class AliasManager {
  private logger = createLogger('AliasManager');
  private aliasFile: string;
  private templateFile: string;
  private aliases: Map<string, Alias> = new Map();
  private templates: Map<string, AliasTemplate> = new Map();

  constructor(configDir?: string) {
    const baseDir = configDir || path.join(process.env.HOME || '/tmp', '.ai-shell');
    this.aliasFile = path.join(baseDir, 'aliases.json');
    this.templateFile = path.join(baseDir, 'alias-templates.json');
  }

  async initialize(): Promise<void> {
    await this.ensureConfigDirectory();
    await this.loadAliases();
    await this.loadTemplates();
    this.logger.info('AliasManager initialized', {
      aliasCount: this.aliases.size,
      templateCount: this.templates.size
    });
  }

  async addAlias(name: string, query: string, options: AddAliasOptions = {}): Promise<void> {
    this.logger.info('Adding alias', { name, query, options });

    // Validate alias name
    if (!this.isValidAliasName(name)) {
      throw new Error(`Invalid alias name: ${name}. Use only alphanumeric characters, hyphens, and underscores.`);
    }

    // Check for existing alias
    if (this.aliases.has(name)) {
      throw new Error(`Alias '${name}' already exists. Use 'edit' to modify or 'remove' to delete it.`);
    }

    // Parse parameters if provided
    const parameters = options.parameters ? this.parseParameters(options.parameters) : undefined;

    // Validate parameter placeholders in query
    if (parameters) {
      this.validateParameterPlaceholders(query, parameters);
    }

    const alias: Alias = {
      name,
      query,
      description: options.description,
      parameters,
      createdAt: new Date(),
      usageCount: 0,
      tags: options.tags
    };

    this.aliases.set(name, alias);
    await this.saveAliases();

    this.logger.info('Alias added successfully', { name });
  }

  async removeAlias(name: string): Promise<void> {
    this.logger.info('Removing alias', { name });

    if (!this.aliases.has(name)) {
      throw new Error(`Alias '${name}' not found.`);
    }

    this.aliases.delete(name);
    await this.saveAliases();

    this.logger.info('Alias removed successfully', { name });
  }

  async listAliases(options: ListAliasOptions = {}): Promise<Alias[]> {
    let aliases = Array.from(this.aliases.values());

    // Filter by tags if provided
    if (options.tags && options.tags.length > 0) {
      aliases = aliases.filter(alias =>
        alias.tags && alias.tags.some(tag => options.tags?.includes(tag))
      );
    }

    // Sort by usage count (descending) then by name
    aliases.sort((a, b) => {
      if (b.usageCount !== a.usageCount) {
        return b.usageCount - a.usageCount;
      }
      return a.name.localeCompare(b.name);
    });

    return aliases;
  }

  async showAlias(name: string): Promise<Alias | null> {
    const alias = this.aliases.get(name);
    if (!alias) {
      return null;
    }
    return { ...alias };
  }

  async editAlias(name: string, updates: Partial<Omit<Alias, 'name' | 'createdAt' | 'usageCount'>>): Promise<void> {
    this.logger.info('Editing alias', { name, updates });

    const alias = this.aliases.get(name);
    if (!alias) {
      throw new Error(`Alias '${name}' not found.`);
    }

    // Update fields
    if (updates.query !== undefined) {
      alias.query = updates.query;
      if (alias.parameters) {
        this.validateParameterPlaceholders(alias.query, alias.parameters);
      }
    }

    if (updates.description !== undefined) {
      alias.description = updates.description;
    }

    if (updates.parameters !== undefined) {
      alias.parameters = updates.parameters;
      if (alias.parameters) {
        this.validateParameterPlaceholders(alias.query, alias.parameters);
      }
    }

    if (updates.tags !== undefined) {
      alias.tags = updates.tags;
    }

    this.aliases.set(name, alias);
    await this.saveAliases();

    this.logger.info('Alias edited successfully', { name });
  }

  async renameAlias(oldName: string, newName: string): Promise<void> {
    this.logger.info('Renaming alias', { oldName, newName });

    if (!this.isValidAliasName(newName)) {
      throw new Error(`Invalid alias name: ${newName}. Use only alphanumeric characters, hyphens, and underscores.`);
    }

    const alias = this.aliases.get(oldName);
    if (!alias) {
      throw new Error(`Alias '${oldName}' not found.`);
    }

    if (this.aliases.has(newName)) {
      throw new Error(`Alias '${newName}' already exists.`);
    }

    const renamedAlias = { ...alias, name: newName };
    this.aliases.delete(oldName);
    this.aliases.set(newName, renamedAlias);
    await this.saveAliases();

    this.logger.info('Alias renamed successfully', { oldName, newName });
  }

  async runAlias(name: string, args: any[] = [], options: RunAliasOptions = {}): Promise<{
    query: string;
    parameters: any[];
    explanation?: string;
  }> {
    this.logger.info('Running alias', { name, args, options });

    const alias = this.aliases.get(name);
    if (!alias) {
      throw new Error(`Alias '${name}' not found.`);
    }

    // Validate and convert parameters
    const parameters = alias.parameters || [];
    const processedArgs = this.processParameters(parameters, args);

    // Substitute parameters in query
    const query = this.substituteParameters(alias.query, processedArgs);

    // Generate explanation if requested
    let explanation: string | undefined;
    if (options.explain) {
      explanation = this.generateExplanation(alias, processedArgs);
    }

    // Update usage statistics (only if not dry-run)
    if (!options.dryRun) {
      alias.lastUsed = new Date();
      alias.usageCount++;
      this.aliases.set(name, alias);
      await this.saveAliases();
    }

    return {
      query,
      parameters: processedArgs,
      explanation
    };
  }

  async exportAliases(file: string, format: 'json' | 'yaml' = 'json'): Promise<void> {
    this.logger.info('Exporting aliases', { file, format });

    const aliases = Array.from(this.aliases.values());
    let content: string;

    if (format === 'yaml') {
      content = yaml.dump(aliases, { indent: 2 });
    } else {
      content = JSON.stringify(aliases, null, 2);
    }

    await fs.writeFile(file, content, 'utf-8');
    this.logger.info('Aliases exported successfully', { file, count: aliases.length });
  }

  async importAliases(file: string, merge: boolean = false): Promise<void> {
    this.logger.info('Importing aliases', { file, merge });

    const content = await fs.readFile(file, 'utf-8');
    let importedAliases: Alias[];

    try {
      // Try JSON first
      importedAliases = JSON.parse(content);
    } catch {
      // Try YAML
      importedAliases = yaml.load(content) as Alias[];
    }

    if (!Array.isArray(importedAliases)) {
      throw new Error('Invalid alias file format. Expected an array of aliases.');
    }

    // Clear existing aliases if not merging
    if (!merge) {
      this.aliases.clear();
    }

    // Import aliases
    for (const alias of importedAliases) {
      // Validate alias structure
      if (!alias.name || !alias.query) {
        this.logger.warn('Skipping invalid alias', { alias });
        continue;
      }

      // Convert date strings to Date objects
      alias.createdAt = new Date(alias.createdAt);
      if (alias.lastUsed) {
        alias.lastUsed = new Date(alias.lastUsed);
      }

      this.aliases.set(alias.name, alias);
    }

    await this.saveAliases();
    this.logger.info('Aliases imported successfully', { count: importedAliases.length });
  }

  // Template methods
  async listTemplates(): Promise<AliasTemplate[]> {
    return Array.from(this.templates.values());
  }

  async createTemplate(template: AliasTemplate): Promise<void> {
    this.logger.info('Creating template', { name: template.name });

    if (!this.isValidAliasName(template.name)) {
      throw new Error(`Invalid template name: ${template.name}`);
    }

    if (this.templates.has(template.name)) {
      throw new Error(`Template '${template.name}' already exists.`);
    }

    this.templates.set(template.name, template);
    await this.saveTemplates();

    this.logger.info('Template created successfully', { name: template.name });
  }

  async fromTemplate(templateName: string, aliasName: string, overrides?: Partial<Alias>): Promise<void> {
    this.logger.info('Creating alias from template', { templateName, aliasName });

    const template = this.templates.get(templateName);
    if (!template) {
      throw new Error(`Template '${templateName}' not found.`);
    }

    if (this.aliases.has(aliasName)) {
      throw new Error(`Alias '${aliasName}' already exists.`);
    }

    const alias: Alias = {
      name: aliasName,
      query: overrides?.query || template.query,
      description: overrides?.description || template.description,
      parameters: overrides?.parameters || template.parameters,
      createdAt: new Date(),
      usageCount: 0,
      tags: overrides?.tags || template.tags
    };

    this.aliases.set(aliasName, alias);
    await this.saveAliases();

    this.logger.info('Alias created from template', { templateName, aliasName });
  }

  // Private helper methods
  private isValidAliasName(name: string): boolean {
    return /^[a-zA-Z0-9_-]+$/.test(name);
  }

  private parseParameters(parametersString: string): AliasParameter[] {
    // Format: "name:type:required:default,name2:type2..."
    const params = parametersString.split(',').map(p => p.trim());
    return params.map(param => {
      const parts = param.split(':');
      if (parts.length < 2) {
        throw new Error(`Invalid parameter format: ${param}. Expected format: name:type[:required][:default]`);
      }

      const [name, type, required = 'true', defaultValue] = parts;

      if (!['string', 'number', 'date', 'boolean'].includes(type)) {
        throw new Error(`Invalid parameter type: ${type}. Must be string, number, date, or boolean.`);
      }

      return {
        name,
        type: type as AliasParameter['type'],
        required: required.toLowerCase() === 'true',
        default: defaultValue !== undefined ? this.convertValue(defaultValue, type as AliasParameter['type']) : undefined
      };
    });
  }

  private validateParameterPlaceholders(query: string, parameters: AliasParameter[]): void {
    // Check that all parameter placeholders ($1, $2, etc.) are valid
    const placeholderRegex = /\$(\d+)/g;
    const matches = query.matchAll(placeholderRegex);

    for (const match of matches) {
      const index = parseInt(match[1], 10);
      if (index < 1 || index > parameters.length) {
        throw new Error(`Invalid parameter placeholder $${index}. Must be between $1 and $${parameters.length}.`);
      }
    }
  }

  private processParameters(parameters: AliasParameter[], args: any[]): any[] {
    const processed: any[] = [];

    for (let i = 0; i < parameters.length; i++) {
      const param = parameters[i];
      const arg = args[i];

      if (arg === undefined || arg === null) {
        if (param.required && param.default === undefined) {
          throw new Error(`Missing required parameter: ${param.name}`);
        }
        processed.push(param.default);
      } else {
        processed.push(this.convertValue(arg, param.type));
      }
    }

    return processed;
  }

  private convertValue(value: any, type: AliasParameter['type']): any {
    try {
      switch (type) {
        case 'number':
          const num = Number(value);
          if (isNaN(num)) {
            throw new Error(`Invalid number: ${value}`);
          }
          return num;
        case 'boolean':
          if (typeof value === 'boolean') return value;
          const lower = String(value).toLowerCase();
          if (['true', '1', 'yes', 'y'].includes(lower)) return true;
          if (['false', '0', 'no', 'n'].includes(lower)) return false;
          throw new Error(`Invalid boolean: ${value}`);
        case 'date':
          const date = new Date(value);
          if (isNaN(date.getTime())) {
            throw new Error(`Invalid date: ${value}`);
          }
          return date.toISOString().split('T')[0]; // Return YYYY-MM-DD format
        case 'string':
        default:
          return String(value);
      }
    } catch (error) {
      throw new Error(`Failed to convert value '${value}' to type '${type}': ${error.message}`);
    }
  }

  private substituteParameters(query: string, parameters: any[]): string {
    let result = query;

    // Replace $1, $2, etc. with actual values
    for (let i = 0; i < parameters.length; i++) {
      const placeholder = `$${i + 1}`;
      const value = parameters[i];

      // Escape single quotes in strings to prevent SQL injection
      const escapedValue = typeof value === 'string'
        ? `'${value.replace(/'/g, "''")}'`
        : value;

      result = result.split(placeholder).join(String(escapedValue));
    }

    return result;
  }

  private generateExplanation(alias: Alias, parameters: any[]): string {
    let explanation = `Alias: ${alias.name}\n`;

    if (alias.description) {
      explanation += `Description: ${alias.description}\n`;
    }

    explanation += `\nQuery Template:\n${alias.query}\n`;

    if (alias.parameters && alias.parameters.length > 0) {
      explanation += `\nParameters:\n`;
      alias.parameters.forEach((param, index) => {
        explanation += `  $${index + 1} (${param.name}: ${param.type}) = ${parameters[index]}\n`;
      });
    }

    explanation += `\nExecuted Query:\n${this.substituteParameters(alias.query, parameters)}`;

    return explanation;
  }

  private async ensureConfigDirectory(): Promise<void> {
    const dir = path.dirname(this.aliasFile);
    try {
      await fs.mkdir(dir, { recursive: true });
    } catch (error) {
      this.logger.warn('Failed to create config directory', { dir, error });
    }
  }

  private async loadAliases(): Promise<void> {
    try {
      const data = await fs.readFile(this.aliasFile, 'utf-8');
      const aliases: Alias[] = JSON.parse(data);

      this.aliases = new Map();
      for (const alias of aliases) {
        // Convert date strings to Date objects
        alias.createdAt = new Date(alias.createdAt);
        if (alias.lastUsed) {
          alias.lastUsed = new Date(alias.lastUsed);
        }
        this.aliases.set(alias.name, alias);
      }

      this.logger.info('Aliases loaded', { count: this.aliases.size });
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
        this.logger.info('No aliases file found, starting with empty aliases');
        this.aliases = new Map();
      } else {
        this.logger.error('Failed to load aliases', { error });
        throw error;
      }
    }
  }

  private async saveAliases(): Promise<void> {
    try {
      const aliases = Array.from(this.aliases.values());
      const data = JSON.stringify(aliases, null, 2);
      await fs.writeFile(this.aliasFile, data, 'utf-8');
      this.logger.debug('Aliases saved', { count: aliases.length });
    } catch (error) {
      this.logger.error('Failed to save aliases', { error });
      throw error;
    }
  }

  private async loadTemplates(): Promise<void> {
    try {
      const data = await fs.readFile(this.templateFile, 'utf-8');
      const templates: AliasTemplate[] = JSON.parse(data);

      this.templates = new Map();
      for (const template of templates) {
        this.templates.set(template.name, template);
      }

      this.logger.info('Templates loaded', { count: this.templates.size });
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
        this.logger.info('No templates file found, initializing with default templates');
        this.templates = new Map();
        await this.initializeDefaultTemplates();
      } else {
        this.logger.error('Failed to load templates', { error });
        throw error;
      }
    }
  }

  private async saveTemplates(): Promise<void> {
    try {
      const templates = Array.from(this.templates.values());
      const data = JSON.stringify(templates, null, 2);
      await fs.writeFile(this.templateFile, data, 'utf-8');
      this.logger.debug('Templates saved', { count: templates.length });
    } catch (error) {
      this.logger.error('Failed to save templates', { error });
      throw error;
    }
  }

  private async initializeDefaultTemplates(): Promise<void> {
    const defaultTemplates: AliasTemplate[] = [
      {
        name: 'user-query',
        description: 'Query user data by ID',
        query: 'SELECT * FROM users WHERE id = $1',
        parameters: [
          { name: 'user_id', type: 'number', required: true }
        ],
        tags: ['user', 'basic']
      },
      {
        name: 'date-range',
        description: 'Query records within a date range',
        query: 'SELECT * FROM records WHERE created_at BETWEEN $1 AND $2',
        parameters: [
          { name: 'start_date', type: 'date', required: true },
          { name: 'end_date', type: 'date', required: true }
        ],
        tags: ['date', 'range']
      },
      {
        name: 'search-text',
        description: 'Search records by text field',
        query: 'SELECT * FROM records WHERE content LIKE $1',
        parameters: [
          { name: 'search_term', type: 'string', required: true }
        ],
        tags: ['search', 'text']
      }
    ];

    for (const template of defaultTemplates) {
      this.templates.set(template.name, template);
    }

    await this.saveTemplates();
  }

  // Statistics methods
  async getStatistics(): Promise<{
    totalAliases: number;
    totalUsage: number;
    mostUsed: Alias[];
    leastUsed: Alias[];
    recentlyCreated: Alias[];
  }> {
    const aliases = Array.from(this.aliases.values());
    const totalUsage = aliases.reduce((sum, alias) => sum + alias.usageCount, 0);

    const sortedByUsage = [...aliases].sort((a, b) => b.usageCount - a.usageCount);
    const sortedByCreation = [...aliases].sort((a, b) =>
      b.createdAt.getTime() - a.createdAt.getTime()
    );

    return {
      totalAliases: aliases.length,
      totalUsage,
      mostUsed: sortedByUsage.slice(0, 5),
      leastUsed: sortedByUsage.slice(-5).reverse(),
      recentlyCreated: sortedByCreation.slice(0, 5)
    };
  }
}
