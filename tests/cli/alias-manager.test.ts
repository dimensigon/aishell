import { describe, it, expect, beforeEach, afterEach } from '@jest/globals';
import { AliasManager, Alias, AliasParameter, AliasTemplate } from '../../src/cli/alias-manager';
import * as fs from 'fs/promises';
import * as path from 'path';
import * as os from 'os';

describe('AliasManager', () => {
  let aliasManager: AliasManager;
  let testConfigDir: string;

  beforeEach(async () => {
    // Create temporary test directory
    testConfigDir = path.join(os.tmpdir(), `ai-shell-test-${Date.now()}`);
    await fs.mkdir(testConfigDir, { recursive: true });

    aliasManager = new AliasManager(testConfigDir);
    await aliasManager.initialize();
  });

  afterEach(async () => {
    // Cleanup test directory
    try {
      await fs.rm(testConfigDir, { recursive: true, force: true });
    } catch (error) {
      // Ignore cleanup errors
    }
  });

  describe('Alias Management', () => {
    describe('addAlias', () => {
      it('should add a simple alias without parameters', async () => {
        await aliasManager.addAlias('test-alias', 'SELECT * FROM users', {
          description: 'Get all users'
        });

        const alias = await aliasManager.showAlias('test-alias');
        expect(alias).toBeDefined();
        expect(alias?.name).toBe('test-alias');
        expect(alias?.query).toBe('SELECT * FROM users');
        expect(alias?.description).toBe('Get all users');
        expect(alias?.usageCount).toBe(0);
      });

      it('should add an alias with parameters', async () => {
        await aliasManager.addAlias(
          'user-by-id',
          'SELECT * FROM users WHERE id = $1',
          {
            description: 'Get user by ID',
            parameters: 'user_id:number:true'
          }
        );

        const alias = await aliasManager.showAlias('user-by-id');
        expect(alias).toBeDefined();
        expect(alias?.parameters).toHaveLength(1);
        expect(alias?.parameters?.[0].name).toBe('user_id');
        expect(alias?.parameters?.[0].type).toBe('number');
        expect(alias?.parameters?.[0].required).toBe(true);
      });

      it('should add an alias with multiple parameters', async () => {
        await aliasManager.addAlias(
          'date-range',
          'SELECT * FROM orders WHERE created_at BETWEEN $1 AND $2',
          {
            parameters: 'start_date:date:true,end_date:date:true'
          }
        );

        const alias = await aliasManager.showAlias('date-range');
        expect(alias?.parameters).toHaveLength(2);
        expect(alias?.parameters?.[0].name).toBe('start_date');
        expect(alias?.parameters?.[0].type).toBe('date');
        expect(alias?.parameters?.[1].name).toBe('end_date');
      });

      it('should add an alias with optional parameters and defaults', async () => {
        await aliasManager.addAlias(
          'user-search',
          'SELECT * FROM users WHERE status = $1 LIMIT $2',
          {
            parameters: 'status:string:false:active,limit:number:false:10'
          }
        );

        const alias = await aliasManager.showAlias('user-search');
        expect(alias?.parameters?.[0].required).toBe(false);
        expect(alias?.parameters?.[0].default).toBe('active');
        expect(alias?.parameters?.[1].default).toBe(10);
      });

      it('should add an alias with tags', async () => {
        await aliasManager.addAlias('tagged-alias', 'SELECT 1', {
          tags: ['test', 'example']
        });

        const alias = await aliasManager.showAlias('tagged-alias');
        expect(alias?.tags).toEqual(['test', 'example']);
      });

      it('should reject invalid alias names', async () => {
        await expect(
          aliasManager.addAlias('invalid name', 'SELECT 1')
        ).rejects.toThrow('Invalid alias name');

        await expect(
          aliasManager.addAlias('invalid@name', 'SELECT 1')
        ).rejects.toThrow('Invalid alias name');
      });

      it('should reject duplicate alias names', async () => {
        await aliasManager.addAlias('duplicate', 'SELECT 1');

        await expect(
          aliasManager.addAlias('duplicate', 'SELECT 2')
        ).rejects.toThrow('already exists');
      });

      it('should validate parameter placeholders', async () => {
        await expect(
          aliasManager.addAlias('invalid-params', 'SELECT * WHERE id = $1 AND name = $3', {
            parameters: 'id:number:true,name:string:true'
          })
        ).rejects.toThrow('Invalid parameter placeholder');
      });

      it('should reject invalid parameter types', async () => {
        await expect(
          aliasManager.addAlias('bad-type', 'SELECT $1', {
            parameters: 'value:invalid:true'
          })
        ).rejects.toThrow('Invalid parameter type');
      });
    });

    describe('removeAlias', () => {
      it('should remove an existing alias', async () => {
        await aliasManager.addAlias('to-remove', 'SELECT 1');
        await aliasManager.removeAlias('to-remove');

        const alias = await aliasManager.showAlias('to-remove');
        expect(alias).toBeNull();
      });

      it('should throw error when removing non-existent alias', async () => {
        await expect(
          aliasManager.removeAlias('non-existent')
        ).rejects.toThrow('not found');
      });
    });

    describe('listAliases', () => {
      it('should list all aliases', async () => {
        await aliasManager.addAlias('alias1', 'SELECT 1');
        await aliasManager.addAlias('alias2', 'SELECT 2');
        await aliasManager.addAlias('alias3', 'SELECT 3');

        const aliases = await aliasManager.listAliases();
        expect(aliases).toHaveLength(3);
      });

      it('should filter aliases by tags', async () => {
        await aliasManager.addAlias('a1', 'SELECT 1', { tags: ['test'] });
        await aliasManager.addAlias('a2', 'SELECT 2', { tags: ['prod'] });
        await aliasManager.addAlias('a3', 'SELECT 3', { tags: ['test', 'prod'] });

        const testAliases = await aliasManager.listAliases({ tags: ['test'] });
        expect(testAliases).toHaveLength(2);
      });

      it('should sort aliases by usage count', async () => {
        await aliasManager.addAlias('low', 'SELECT 1');
        await aliasManager.addAlias('high', 'SELECT 2');

        // Run high usage alias multiple times
        await aliasManager.runAlias('high');
        await aliasManager.runAlias('high');
        await aliasManager.runAlias('high');
        await aliasManager.runAlias('low');

        const aliases = await aliasManager.listAliases();
        expect(aliases[0].name).toBe('high');
        expect(aliases[1].name).toBe('low');
      });
    });

    describe('editAlias', () => {
      it('should update alias query', async () => {
        await aliasManager.addAlias('editable', 'SELECT 1');
        await aliasManager.editAlias('editable', { query: 'SELECT 2' });

        const alias = await aliasManager.showAlias('editable');
        expect(alias?.query).toBe('SELECT 2');
      });

      it('should update alias description', async () => {
        await aliasManager.addAlias('editable', 'SELECT 1');
        await aliasManager.editAlias('editable', { description: 'New description' });

        const alias = await aliasManager.showAlias('editable');
        expect(alias?.description).toBe('New description');
      });

      it('should update alias tags', async () => {
        await aliasManager.addAlias('editable', 'SELECT 1');
        await aliasManager.editAlias('editable', { tags: ['new', 'tags'] });

        const alias = await aliasManager.showAlias('editable');
        expect(alias?.tags).toEqual(['new', 'tags']);
      });

      it('should throw error when editing non-existent alias', async () => {
        await expect(
          aliasManager.editAlias('non-existent', { query: 'SELECT 1' })
        ).rejects.toThrow('not found');
      });
    });

    describe('renameAlias', () => {
      it('should rename an alias', async () => {
        await aliasManager.addAlias('old-name', 'SELECT 1');
        await aliasManager.renameAlias('old-name', 'new-name');

        const oldAlias = await aliasManager.showAlias('old-name');
        const newAlias = await aliasManager.showAlias('new-name');

        expect(oldAlias).toBeNull();
        expect(newAlias).toBeDefined();
        expect(newAlias?.name).toBe('new-name');
      });

      it('should reject rename to invalid name', async () => {
        await aliasManager.addAlias('valid', 'SELECT 1');

        await expect(
          aliasManager.renameAlias('valid', 'invalid name')
        ).rejects.toThrow('Invalid alias name');
      });

      it('should reject rename to existing name', async () => {
        await aliasManager.addAlias('name1', 'SELECT 1');
        await aliasManager.addAlias('name2', 'SELECT 2');

        await expect(
          aliasManager.renameAlias('name1', 'name2')
        ).rejects.toThrow('already exists');
      });
    });
  });

  describe('Parameter Substitution', () => {
    it('should substitute string parameters', async () => {
      await aliasManager.addAlias('string-test', 'SELECT * FROM users WHERE name = $1', {
        parameters: 'name:string:true'
      });

      const result = await aliasManager.runAlias('string-test', ['John']);
      expect(result.query).toBe("SELECT * FROM users WHERE name = 'John'");
    });

    it('should substitute number parameters', async () => {
      await aliasManager.addAlias('number-test', 'SELECT * FROM users WHERE id = $1', {
        parameters: 'id:number:true'
      });

      const result = await aliasManager.runAlias('number-test', [42]);
      expect(result.query).toBe('SELECT * FROM users WHERE id = 42');
    });

    it('should substitute date parameters', async () => {
      await aliasManager.addAlias('date-test', 'SELECT * FROM orders WHERE date = $1', {
        parameters: 'date:date:true'
      });

      const result = await aliasManager.runAlias('date-test', ['2025-01-15']);
      expect(result.query).toContain('2025-01-15');
    });

    it('should substitute boolean parameters', async () => {
      await aliasManager.addAlias('bool-test', 'SELECT * FROM users WHERE active = $1', {
        parameters: 'active:boolean:true'
      });

      const result = await aliasManager.runAlias('bool-test', [true]);
      expect(result.query).toBe('SELECT * FROM users WHERE active = true');
    });

    it('should use default values for missing optional parameters', async () => {
      await aliasManager.addAlias('default-test', 'SELECT * FROM users LIMIT $1', {
        parameters: 'limit:number:false:10'
      });

      const result = await aliasManager.runAlias('default-test', []);
      expect(result.query).toBe('SELECT * FROM users LIMIT 10');
    });

    it('should escape single quotes in string parameters', async () => {
      await aliasManager.addAlias('escape-test', 'SELECT * FROM users WHERE name = $1', {
        parameters: 'name:string:true'
      });

      const result = await aliasManager.runAlias('escape-test', ["O'Brien"]);
      expect(result.query).toBe("SELECT * FROM users WHERE name = 'O''Brien'");
    });

    it('should handle multiple parameters', async () => {
      await aliasManager.addAlias(
        'multi-param',
        'SELECT * FROM orders WHERE user_id = $1 AND date BETWEEN $2 AND $3',
        {
          parameters: 'user_id:number:true,start:date:true,end:date:true'
        }
      );

      const result = await aliasManager.runAlias('multi-param', [123, '2025-01-01', '2025-01-31']);
      expect(result.query).toContain('123');
      expect(result.query).toContain('2025-01-01');
      expect(result.query).toContain('2025-01-31');
    });

    it('should throw error for missing required parameters', async () => {
      await aliasManager.addAlias('required-test', 'SELECT * FROM users WHERE id = $1', {
        parameters: 'id:number:true'
      });

      await expect(
        aliasManager.runAlias('required-test', [])
      ).rejects.toThrow('Missing required parameter');
    });

    it('should throw error for invalid parameter types', async () => {
      await aliasManager.addAlias('type-test', 'SELECT * FROM users WHERE id = $1', {
        parameters: 'id:number:true'
      });

      await expect(
        aliasManager.runAlias('type-test', ['not-a-number'])
      ).rejects.toThrow('Invalid number');
    });
  });

  describe('Alias Execution', () => {
    it('should track usage count', async () => {
      await aliasManager.addAlias('usage-test', 'SELECT 1');

      await aliasManager.runAlias('usage-test');
      await aliasManager.runAlias('usage-test');
      await aliasManager.runAlias('usage-test');

      const alias = await aliasManager.showAlias('usage-test');
      expect(alias?.usageCount).toBe(3);
    });

    it('should track last used timestamp', async () => {
      await aliasManager.addAlias('timestamp-test', 'SELECT 1');

      const before = new Date();
      await aliasManager.runAlias('timestamp-test');
      const after = new Date();

      const alias = await aliasManager.showAlias('timestamp-test');
      expect(alias?.lastUsed).toBeDefined();
      expect(alias?.lastUsed!.getTime()).toBeGreaterThanOrEqual(before.getTime());
      expect(alias?.lastUsed!.getTime()).toBeLessThanOrEqual(after.getTime());
    });

    it('should generate explanation when requested', async () => {
      await aliasManager.addAlias('explain-test', 'SELECT * FROM users WHERE id = $1', {
        description: 'Get user by ID',
        parameters: 'id:number:true'
      });

      const result = await aliasManager.runAlias('explain-test', [42], { explain: true });

      expect(result.explanation).toBeDefined();
      expect(result.explanation).toContain('explain-test');
      expect(result.explanation).toContain('Get user by ID');
      expect(result.explanation).toContain('42');
    });

    it('should not update statistics in dry-run mode', async () => {
      await aliasManager.addAlias('dryrun-test', 'SELECT 1');

      await aliasManager.runAlias('dryrun-test', [], { dryRun: true });

      const alias = await aliasManager.showAlias('dryrun-test');
      expect(alias?.usageCount).toBe(0);
      expect(alias?.lastUsed).toBeUndefined();
    });
  });

  describe('Export and Import', () => {
    it('should export aliases to JSON', async () => {
      await aliasManager.addAlias('export1', 'SELECT 1');
      await aliasManager.addAlias('export2', 'SELECT 2');

      const exportFile = path.join(testConfigDir, 'export.json');
      await aliasManager.exportAliases(exportFile, 'json');

      const content = await fs.readFile(exportFile, 'utf-8');
      const exported = JSON.parse(content);

      expect(exported).toHaveLength(2);
      expect(exported.find((a: Alias) => a.name === 'export1')).toBeDefined();
      expect(exported.find((a: Alias) => a.name === 'export2')).toBeDefined();
    });

    it('should export aliases to YAML', async () => {
      await aliasManager.addAlias('yaml1', 'SELECT 1');

      const exportFile = path.join(testConfigDir, 'export.yaml');
      await aliasManager.exportAliases(exportFile, 'yaml');

      const content = await fs.readFile(exportFile, 'utf-8');
      expect(content).toContain('yaml1');
      expect(content).toContain('SELECT 1');
    });

    it('should import aliases from JSON', async () => {
      const importData = [
        {
          name: 'imported1',
          query: 'SELECT 1',
          description: 'Imported alias',
          createdAt: new Date().toISOString(),
          usageCount: 0
        }
      ];

      const importFile = path.join(testConfigDir, 'import.json');
      await fs.writeFile(importFile, JSON.stringify(importData));

      await aliasManager.importAliases(importFile);

      const alias = await aliasManager.showAlias('imported1');
      expect(alias).toBeDefined();
      expect(alias?.description).toBe('Imported alias');
    });

    it('should merge imported aliases when specified', async () => {
      await aliasManager.addAlias('existing', 'SELECT 1');

      const importData = [
        {
          name: 'new-alias',
          query: 'SELECT 2',
          createdAt: new Date().toISOString(),
          usageCount: 0
        }
      ];

      const importFile = path.join(testConfigDir, 'import.json');
      await fs.writeFile(importFile, JSON.stringify(importData));

      await aliasManager.importAliases(importFile, true);

      const existing = await aliasManager.showAlias('existing');
      const newAlias = await aliasManager.showAlias('new-alias');

      expect(existing).toBeDefined();
      expect(newAlias).toBeDefined();
    });

    it('should replace aliases when merge is false', async () => {
      await aliasManager.addAlias('existing', 'SELECT 1');

      const importData = [
        {
          name: 'new-alias',
          query: 'SELECT 2',
          createdAt: new Date().toISOString(),
          usageCount: 0
        }
      ];

      const importFile = path.join(testConfigDir, 'import.json');
      await fs.writeFile(importFile, JSON.stringify(importData));

      await aliasManager.importAliases(importFile, false);

      const existing = await aliasManager.showAlias('existing');
      const newAlias = await aliasManager.showAlias('new-alias');

      expect(existing).toBeNull();
      expect(newAlias).toBeDefined();
    });
  });

  describe('Templates', () => {
    it('should create a template', async () => {
      await aliasManager.createTemplate({
        name: 'test-template',
        description: 'Test template',
        query: 'SELECT * FROM users WHERE id = $1',
        parameters: [
          { name: 'user_id', type: 'number', required: true }
        ]
      });

      const templates = await aliasManager.listTemplates();
      expect(templates.find(t => t.name === 'test-template')).toBeDefined();
    });

    it('should create alias from template', async () => {
      await aliasManager.createTemplate({
        name: 'user-template',
        description: 'User query template',
        query: 'SELECT * FROM users WHERE id = $1',
        parameters: [
          { name: 'user_id', type: 'number', required: true }
        ],
        tags: ['user']
      });

      await aliasManager.fromTemplate('user-template', 'my-user-alias');

      const alias = await aliasManager.showAlias('my-user-alias');
      expect(alias).toBeDefined();
      expect(alias?.query).toBe('SELECT * FROM users WHERE id = $1');
      expect(alias?.tags).toEqual(['user']);
    });

    it('should have default templates after initialization', async () => {
      const templates = await aliasManager.listTemplates();
      expect(templates.length).toBeGreaterThan(0);
    });
  });

  describe('Statistics', () => {
    it('should return correct statistics', async () => {
      await aliasManager.addAlias('stats1', 'SELECT 1');
      await aliasManager.addAlias('stats2', 'SELECT 2');
      await aliasManager.addAlias('stats3', 'SELECT 3');

      await aliasManager.runAlias('stats1');
      await aliasManager.runAlias('stats1');
      await aliasManager.runAlias('stats2');

      const stats = await aliasManager.getStatistics();

      expect(stats.totalAliases).toBe(3);
      expect(stats.totalUsage).toBe(3);
      expect(stats.mostUsed[0].name).toBe('stats1');
      expect(stats.mostUsed[0].usageCount).toBe(2);
    });

    it('should show least used aliases', async () => {
      await aliasManager.addAlias('used', 'SELECT 1');
      await aliasManager.addAlias('unused', 'SELECT 2');

      await aliasManager.runAlias('used');
      await aliasManager.runAlias('used');

      const stats = await aliasManager.getStatistics();
      expect(stats.leastUsed[0].name).toBe('unused');
      expect(stats.leastUsed[0].usageCount).toBe(0);
    });

    it('should show recently created aliases', async () => {
      await aliasManager.addAlias('old', 'SELECT 1');
      await new Promise(resolve => setTimeout(resolve, 10));
      await aliasManager.addAlias('new', 'SELECT 2');

      const stats = await aliasManager.getStatistics();
      expect(stats.recentlyCreated[0].name).toBe('new');
    });
  });

  describe('Persistence', () => {
    it('should persist aliases to disk', async () => {
      await aliasManager.addAlias('persistent', 'SELECT 1');

      // Create new instance with same config dir
      const newManager = new AliasManager(testConfigDir);
      await newManager.initialize();

      const alias = await newManager.showAlias('persistent');
      expect(alias).toBeDefined();
      expect(alias?.name).toBe('persistent');
    });

    it('should persist templates to disk', async () => {
      await aliasManager.createTemplate({
        name: 'persistent-template',
        description: 'Test',
        query: 'SELECT 1'
      });

      const newManager = new AliasManager(testConfigDir);
      await newManager.initialize();

      const templates = await newManager.listTemplates();
      expect(templates.find(t => t.name === 'persistent-template')).toBeDefined();
    });
  });
});
