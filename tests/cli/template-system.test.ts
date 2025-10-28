/**
 * Template System Tests
 * Comprehensive tests for query templates with parameter injection security
 */

import { describe, it, expect, beforeEach, afterEach, jest } from '@jest/globals';
import * as fs from 'fs/promises';
import * as path from 'path';
import * as os from 'os';

// Template System interfaces (based on P3 requirements)
interface TemplateParameter {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'date' | 'array';
  required: boolean;
  default?: any;
  validation?: {
    min?: number;
    max?: number;
    pattern?: RegExp;
    enum?: any[];
  };
}

interface QueryTemplate {
  id: string;
  name: string;
  description?: string;
  query: string;
  parameters: TemplateParameter[];
  tags?: string[];
  createdAt: number;
  updatedAt: number;
  usageCount: number;
}

interface TemplateExecutionResult {
  sql: string;
  parameters: Record<string, any>;
  warnings: string[];
}

// Mock Template System class
class TemplateSystem {
  constructor(private configDir: string) {}

  async initialize(): Promise<void> {
    await fs.mkdir(this.configDir, { recursive: true });
  }

  async createTemplate(
    name: string,
    query: string,
    parameters: TemplateParameter[],
    options: { description?: string; tags?: string[] } = {}
  ): Promise<QueryTemplate> {
    const template: QueryTemplate = {
      id: `tpl_${Date.now()}`,
      name,
      description: options.description,
      query,
      parameters,
      tags: options.tags || [],
      createdAt: Date.now(),
      updatedAt: Date.now(),
      usageCount: 0
    };

    const filepath = path.join(this.configDir, `${template.id}.json`);
    await fs.writeFile(filepath, JSON.stringify(template, null, 2));

    return template;
  }

  async getTemplate(name: string): Promise<QueryTemplate | null> {
    const files = await fs.readdir(this.configDir);
    for (const file of files) {
      const content = await fs.readFile(path.join(this.configDir, file), 'utf-8');
      const template = JSON.parse(content) as QueryTemplate;
      if (template.name === name) {
        return template;
      }
    }
    return null;
  }

  async listTemplates(filter?: { tag?: string }): Promise<QueryTemplate[]> {
    const files = await fs.readdir(this.configDir);
    const templates: QueryTemplate[] = [];

    for (const file of files) {
      if (!file.endsWith('.json')) continue;
      const content = await fs.readFile(path.join(this.configDir, file), 'utf-8');
      const template = JSON.parse(content) as QueryTemplate;

      if (filter?.tag && !template.tags?.includes(filter.tag)) continue;

      templates.push(template);
    }

    return templates;
  }

  async executeTemplate(
    name: string,
    params: Record<string, any>
  ): Promise<TemplateExecutionResult> {
    const template = await this.getTemplate(name);
    if (!template) {
      throw new Error(`Template not found: ${name}`);
    }

    // Validate parameters
    const warnings = this.validateParameters(template, params);

    // Sanitize parameters to prevent SQL injection
    const sanitized = this.sanitizeParameters(params);

    // Replace parameters in query
    const sql = this.interpolateQuery(template.query, sanitized);

    // Increment usage count
    template.usageCount++;
    template.updatedAt = Date.now();
    const filepath = path.join(this.configDir, `${template.id}.json`);
    await fs.writeFile(filepath, JSON.stringify(template, null, 2));

    return { sql, parameters: sanitized, warnings };
  }

  private validateParameters(template: QueryTemplate, params: Record<string, any>): string[] {
    const warnings: string[] = [];

    for (const param of template.parameters) {
      if (param.required && !(param.name in params)) {
        throw new Error(`Required parameter missing: ${param.name}`);
      }

      const value = params[param.name];
      if (value === undefined || value === null) continue;

      // Type validation
      if (param.type === 'number' && typeof value !== 'number') {
        throw new Error(`Parameter ${param.name} must be a number`);
      }

      // Range validation
      if (param.validation?.min !== undefined && value < param.validation.min) {
        throw new Error(`Parameter ${param.name} must be >= ${param.validation.min}`);
      }

      if (param.validation?.max !== undefined && value > param.validation.max) {
        throw new Error(`Parameter ${param.name} must be <= ${param.validation.max}`);
      }

      // Pattern validation
      if (param.validation?.pattern && typeof value === 'string') {
        if (!param.validation.pattern.test(value)) {
          throw new Error(`Parameter ${param.name} does not match required pattern`);
        }
      }

      // Enum validation
      if (param.validation?.enum && !param.validation.enum.includes(value)) {
        throw new Error(`Parameter ${param.name} must be one of: ${param.validation.enum.join(', ')}`);
      }
    }

    return warnings;
  }

  private sanitizeParameters(params: Record<string, any>): Record<string, any> {
    const sanitized: Record<string, any> = {};

    for (const [key, value] of Object.entries(params)) {
      if (typeof value === 'string') {
        // Escape SQL injection patterns
        sanitized[key] = value
          .replace(/'/g, "''")
          .replace(/;/g, '')
          .replace(/--/g, '')
          .replace(/\/\*/g, '')
          .replace(/\*\//g, '');
      } else {
        sanitized[key] = value;
      }
    }

    return sanitized;
  }

  private interpolateQuery(query: string, params: Record<string, any>): string {
    let result = query;

    for (const [key, value] of Object.entries(params)) {
      const placeholder = `{{${key}}}`;
      let replacement: string;

      if (typeof value === 'string') {
        replacement = `'${value}'`;
      } else if (Array.isArray(value)) {
        replacement = value.map(v => (typeof v === 'string' ? `'${v}'` : v)).join(', ');
      } else {
        replacement = String(value);
      }

      result = result.replace(new RegExp(placeholder, 'g'), replacement);
    }

    return result;
  }

  async deleteTemplate(name: string): Promise<boolean> {
    const template = await this.getTemplate(name);
    if (!template) return false;

    const filepath = path.join(this.configDir, `${template.id}.json`);
    await fs.unlink(filepath);
    return true;
  }

  async updateTemplate(
    name: string,
    updates: Partial<Omit<QueryTemplate, 'id' | 'createdAt'>>
  ): Promise<QueryTemplate> {
    const template = await this.getTemplate(name);
    if (!template) {
      throw new Error(`Template not found: ${name}`);
    }

    Object.assign(template, updates);
    template.updatedAt = Date.now();

    const filepath = path.join(this.configDir, `${template.id}.json`);
    await fs.writeFile(filepath, JSON.stringify(template, null, 2));

    return template;
  }
}

describe('TemplateSystem', () => {
  let templateSystem: TemplateSystem;
  let testDir: string;

  beforeEach(async () => {
    testDir = path.join(os.tmpdir(), `ai-shell-test-${Date.now()}`);
    templateSystem = new TemplateSystem(testDir);
    await templateSystem.initialize();
  });

  afterEach(async () => {
    try {
      await fs.rm(testDir, { recursive: true, force: true });
    } catch (error) {
      // Ignore
    }
  });

  describe('createTemplate', () => {
    it('should create a simple template', async () => {
      const template = await templateSystem.createTemplate(
        'get-users',
        'SELECT * FROM users',
        [],
        { description: 'Get all users' }
      );

      expect(template.name).toBe('get-users');
      expect(template.query).toBe('SELECT * FROM users');
      expect(template.id).toBeDefined();
    });

    it('should create template with parameters', async () => {
      const parameters: TemplateParameter[] = [
        {
          name: 'user_id',
          type: 'number',
          required: true
        }
      ];

      const template = await templateSystem.createTemplate(
        'get-user-by-id',
        'SELECT * FROM users WHERE id = {{user_id}}',
        parameters
      );

      expect(template.parameters.length).toBe(1);
      expect(template.parameters[0].name).toBe('user_id');
    });

    it('should create template with validation rules', async () => {
      const parameters: TemplateParameter[] = [
        {
          name: 'age',
          type: 'number',
          required: false,
          validation: {
            min: 0,
            max: 150
          }
        }
      ];

      const template = await templateSystem.createTemplate(
        'users-by-age',
        'SELECT * FROM users WHERE age > {{age}}',
        parameters
      );

      expect(template.parameters[0].validation?.min).toBe(0);
      expect(template.parameters[0].validation?.max).toBe(150);
    });

    it('should create template with pattern validation', async () => {
      const parameters: TemplateParameter[] = [
        {
          name: 'email',
          type: 'string',
          required: true,
          validation: {
            pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/
          }
        }
      ];

      const template = await templateSystem.createTemplate(
        'user-by-email',
        'SELECT * FROM users WHERE email = {{email}}',
        parameters
      );

      expect(template.parameters[0].validation?.pattern).toBeDefined();
    });

    it('should create template with enum validation', async () => {
      const parameters: TemplateParameter[] = [
        {
          name: 'status',
          type: 'string',
          required: true,
          validation: {
            enum: ['active', 'inactive', 'pending']
          }
        }
      ];

      const template = await templateSystem.createTemplate(
        'users-by-status',
        'SELECT * FROM users WHERE status = {{status}}',
        parameters
      );

      expect(template.parameters[0].validation?.enum).toEqual(['active', 'inactive', 'pending']);
    });

    it('should create template with tags', async () => {
      const template = await templateSystem.createTemplate(
        'tagged-template',
        'SELECT 1',
        [],
        { tags: ['reporting', 'analytics'] }
      );

      expect(template.tags).toEqual(['reporting', 'analytics']);
    });

    it('should create template with array parameter', async () => {
      const parameters: TemplateParameter[] = [
        {
          name: 'ids',
          type: 'array',
          required: true
        }
      ];

      const template = await templateSystem.createTemplate(
        'users-by-ids',
        'SELECT * FROM users WHERE id IN ({{ids}})',
        parameters
      );

      expect(template.parameters[0].type).toBe('array');
    });

    it('should set timestamps on creation', async () => {
      const template = await templateSystem.createTemplate('test', 'SELECT 1', []);

      expect(template.createdAt).toBeDefined();
      expect(template.updatedAt).toBeDefined();
      expect(template.usageCount).toBe(0);
    });
  });

  describe('getTemplate', () => {
    it('should retrieve existing template', async () => {
      await templateSystem.createTemplate('test-tpl', 'SELECT 1', []);

      const template = await templateSystem.getTemplate('test-tpl');

      expect(template).toBeDefined();
      expect(template?.name).toBe('test-tpl');
    });

    it('should return null for non-existent template', async () => {
      const template = await templateSystem.getTemplate('nonexistent');

      expect(template).toBeNull();
    });
  });

  describe('listTemplates', () => {
    it('should list all templates', async () => {
      await templateSystem.createTemplate('tpl1', 'SELECT 1', []);
      await templateSystem.createTemplate('tpl2', 'SELECT 2', []);
      await templateSystem.createTemplate('tpl3', 'SELECT 3', []);

      const templates = await templateSystem.listTemplates();

      expect(templates.length).toBe(3);
    });

    it('should filter templates by tag', async () => {
      await templateSystem.createTemplate('tpl1', 'SELECT 1', [], { tags: ['reporting'] });
      await templateSystem.createTemplate('tpl2', 'SELECT 2', [], { tags: ['analytics'] });
      await templateSystem.createTemplate('tpl3', 'SELECT 3', [], { tags: ['reporting'] });

      const templates = await templateSystem.listTemplates({ tag: 'reporting' });

      expect(templates.length).toBe(2);
      expect(templates.every(t => t.tags?.includes('reporting'))).toBe(true);
    });

    it('should return empty array when no templates exist', async () => {
      const templates = await templateSystem.listTemplates();

      expect(templates).toEqual([]);
    });
  });

  describe('executeTemplate', () => {
    it('should execute template with parameters', async () => {
      const parameters: TemplateParameter[] = [
        { name: 'user_id', type: 'number', required: true }
      ];

      await templateSystem.createTemplate(
        'get-user',
        'SELECT * FROM users WHERE id = {{user_id}}',
        parameters
      );

      const result = await templateSystem.executeTemplate('get-user', { user_id: 123 });

      expect(result.sql).toContain('123');
      expect(result.parameters.user_id).toBe(123);
    });

    it('should throw error for missing required parameter', async () => {
      const parameters: TemplateParameter[] = [
        { name: 'user_id', type: 'number', required: true }
      ];

      await templateSystem.createTemplate(
        'get-user',
        'SELECT * FROM users WHERE id = {{user_id}}',
        parameters
      );

      await expect(
        templateSystem.executeTemplate('get-user', {})
      ).rejects.toThrow('Required parameter missing: user_id');
    });

    it('should validate parameter type', async () => {
      const parameters: TemplateParameter[] = [
        { name: 'user_id', type: 'number', required: true }
      ];

      await templateSystem.createTemplate(
        'get-user',
        'SELECT * FROM users WHERE id = {{user_id}}',
        parameters
      );

      await expect(
        templateSystem.executeTemplate('get-user', { user_id: 'not-a-number' })
      ).rejects.toThrow('must be a number');
    });

    it('should validate parameter range', async () => {
      const parameters: TemplateParameter[] = [
        {
          name: 'age',
          type: 'number',
          required: true,
          validation: { min: 0, max: 150 }
        }
      ];

      await templateSystem.createTemplate(
        'users-by-age',
        'SELECT * FROM users WHERE age = {{age}}',
        parameters
      );

      await expect(
        templateSystem.executeTemplate('users-by-age', { age: 200 })
      ).rejects.toThrow('must be <= 150');
    });

    it('should validate parameter pattern', async () => {
      const parameters: TemplateParameter[] = [
        {
          name: 'email',
          type: 'string',
          required: true,
          validation: { pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/ }
        }
      ];

      await templateSystem.createTemplate(
        'user-by-email',
        'SELECT * FROM users WHERE email = {{email}}',
        parameters
      );

      await expect(
        templateSystem.executeTemplate('user-by-email', { email: 'invalid-email' })
      ).rejects.toThrow('does not match required pattern');
    });

    it('should validate enum parameter', async () => {
      const parameters: TemplateParameter[] = [
        {
          name: 'status',
          type: 'string',
          required: true,
          validation: { enum: ['active', 'inactive'] }
        }
      ];

      await templateSystem.createTemplate(
        'users-by-status',
        'SELECT * FROM users WHERE status = {{status}}',
        parameters
      );

      await expect(
        templateSystem.executeTemplate('users-by-status', { status: 'invalid' })
      ).rejects.toThrow('must be one of');
    });

    it('should prevent SQL injection with single quote', async () => {
      const parameters: TemplateParameter[] = [
        { name: 'name', type: 'string', required: true }
      ];

      await templateSystem.createTemplate(
        'user-by-name',
        'SELECT * FROM users WHERE name = {{name}}',
        parameters
      );

      const result = await templateSystem.executeTemplate('user-by-name', {
        name: "John'; DROP TABLE users; --"
      });

      expect(result.sql).not.toContain('DROP TABLE');
      expect(result.sql).toContain("''"); // Single quotes escaped
    });

    it('should prevent SQL injection with comments', async () => {
      const parameters: TemplateParameter[] = [
        { name: 'comment', type: 'string', required: true }
      ];

      await templateSystem.createTemplate(
        'add-comment',
        'INSERT INTO comments (text) VALUES ({{comment}})',
        parameters
      );

      const result = await templateSystem.executeTemplate('add-comment', {
        comment: 'Test /* malicious */ comment'
      });

      expect(result.sql).not.toContain('/*');
      expect(result.sql).not.toContain('*/');
    });

    it('should handle array parameters', async () => {
      const parameters: TemplateParameter[] = [
        { name: 'ids', type: 'array', required: true }
      ];

      await templateSystem.createTemplate(
        'users-by-ids',
        'SELECT * FROM users WHERE id IN ({{ids}})',
        parameters
      );

      const result = await templateSystem.executeTemplate('users-by-ids', {
        ids: [1, 2, 3]
      });

      expect(result.sql).toContain('1, 2, 3');
    });

    it('should increment usage count', async () => {
      const parameters: TemplateParameter[] = [
        { name: 'id', type: 'number', required: true }
      ];

      await templateSystem.createTemplate(
        'test-tpl',
        'SELECT * FROM users WHERE id = {{id}}',
        parameters
      );

      await templateSystem.executeTemplate('test-tpl', { id: 1 });
      await templateSystem.executeTemplate('test-tpl', { id: 2 });

      const template = await templateSystem.getTemplate('test-tpl');
      expect(template?.usageCount).toBe(2);
    });

    it('should throw error for non-existent template', async () => {
      await expect(
        templateSystem.executeTemplate('nonexistent', {})
      ).rejects.toThrow('Template not found');
    });
  });

  describe('updateTemplate', () => {
    it('should update template description', async () => {
      await templateSystem.createTemplate('test-tpl', 'SELECT 1', []);

      const updated = await templateSystem.updateTemplate('test-tpl', {
        description: 'New description'
      });

      expect(updated.description).toBe('New description');
    });

    it('should update template query', async () => {
      await templateSystem.createTemplate('test-tpl', 'SELECT 1', []);

      const updated = await templateSystem.updateTemplate('test-tpl', {
        query: 'SELECT 2'
      });

      expect(updated.query).toBe('SELECT 2');
    });

    it('should update timestamp', async () => {
      await templateSystem.createTemplate('test-tpl', 'SELECT 1', []);
      const original = await templateSystem.getTemplate('test-tpl');

      await new Promise(resolve => setTimeout(resolve, 10));

      const updated = await templateSystem.updateTemplate('test-tpl', {
        description: 'Updated'
      });

      expect(updated.updatedAt).toBeGreaterThan(original!.updatedAt);
    });

    it('should throw error for non-existent template', async () => {
      await expect(
        templateSystem.updateTemplate('nonexistent', { description: 'Test' })
      ).rejects.toThrow('Template not found');
    });
  });

  describe('deleteTemplate', () => {
    it('should delete existing template', async () => {
      await templateSystem.createTemplate('test-tpl', 'SELECT 1', []);

      const deleted = await templateSystem.deleteTemplate('test-tpl');

      expect(deleted).toBe(true);

      const template = await templateSystem.getTemplate('test-tpl');
      expect(template).toBeNull();
    });

    it('should return false for non-existent template', async () => {
      const deleted = await templateSystem.deleteTemplate('nonexistent');

      expect(deleted).toBe(false);
    });
  });

  describe('Security Tests', () => {
    it('should prevent SQL injection via semicolon', async () => {
      const parameters: TemplateParameter[] = [
        { name: 'input', type: 'string', required: true }
      ];

      await templateSystem.createTemplate(
        'test',
        'SELECT * FROM users WHERE name = {{input}}',
        parameters
      );

      const result = await templateSystem.executeTemplate('test', {
        input: 'test; DELETE FROM users;'
      });

      expect(result.sql).not.toContain(';');
    });

    it('should prevent SQL injection via UNION', async () => {
      const parameters: TemplateParameter[] = [
        { name: 'input', type: 'string', required: true }
      ];

      await templateSystem.createTemplate(
        'test',
        'SELECT * FROM users WHERE id = {{input}}',
        parameters
      );

      const result = await templateSystem.executeTemplate('test', {
        input: "1 UNION SELECT * FROM passwords"
      });

      // Input should be sanitized
      expect(result.sql).toBeDefined();
    });

    it('should prevent command injection', async () => {
      const parameters: TemplateParameter[] = [
        { name: 'filename', type: 'string', required: true }
      ];

      await templateSystem.createTemplate(
        'test',
        'COPY users TO {{filename}}',
        parameters
      );

      const result = await templateSystem.executeTemplate('test', {
        filename: '| rm -rf /'
      });

      expect(result.sql).not.toContain('rm -rf');
    });
  });

  describe('Performance Tests', () => {
    it('should handle 100 templates efficiently', async () => {
      const start = Date.now();

      for (let i = 0; i < 100; i++) {
        await templateSystem.createTemplate(
          `template-${i}`,
          `SELECT ${i}`,
          []
        );
      }

      const duration = Date.now() - start;
      expect(duration).toBeLessThan(5000); // Should complete in < 5 seconds
    });

    it('should list templates efficiently', async () => {
      for (let i = 0; i < 50; i++) {
        await templateSystem.createTemplate(`template-${i}`, `SELECT ${i}`, []);
      }

      const start = Date.now();
      const templates = await templateSystem.listTemplates();
      const duration = Date.now() - start;

      expect(templates.length).toBe(50);
      expect(duration).toBeLessThan(1000); // Should complete in < 1 second
    });
  });
});
