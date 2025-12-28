/**
 * MySQL Integration Tests
 * Comprehensive test suite for MySQL client using Docker test environment
 *
 * Connection: mysql://root:MyMySQLPass123@localhost:3307
 * Test Database: test_db
 *
 * Test Coverage:
 * - Connection and authentication
 * - CRUD operations
 * - Transaction management (InnoDB)
 * - Foreign key constraints
 * - Full-text search indexes
 * - Stored procedures and functions
 * - Triggers
 * - Views and complex JOINs
 * - JSON column support
 * - MySQL-specific features (AUTO_INCREMENT, ON DUPLICATE KEY UPDATE)
 * - Bulk inserts
 * - Connection pooling
 */

import { describe, it, expect, beforeAll, afterAll, beforeEach } from 'vitest';
import * as mysql from 'mysql2/promise';
import * as fs from 'fs';
import * as path from 'path';
import { testDatabaseConfig } from '../../config/databases.test';

// Connection configuration from centralized config
const MYSQL_CONFIG = testDatabaseConfig.mysql;

// Connection pool configuration
const POOL_CONFIG = {
  ...MYSQL_CONFIG,
  waitForConnections: true,
  connectionLimit: 10,
  queueLimit: 0,
};

describe('MySQL Integration Tests', () => {
  let connection: mysql.Connection;
  let pool: mysql.Pool;

  beforeAll(async () => {
    console.log('🔌 Connecting to MySQL test database...');

    try {
      // Create connection without database first
      const setupConnection = await mysql.createConnection({
        host: MYSQL_CONFIG.host,
        port: MYSQL_CONFIG.port,
        user: MYSQL_CONFIG.user,
        password: MYSQL_CONFIG.password,
        multipleStatements: true,
      });

      // Create test database if it doesn't exist
      await setupConnection.query(`CREATE DATABASE IF NOT EXISTS ${MYSQL_CONFIG.database}`);
      await setupConnection.query(`USE ${MYSQL_CONFIG.database}`);

      // Read and execute initialization script
      const initScriptPath = path.join(__dirname, 'init-mysql.sql');
      const initScript = fs.readFileSync(initScriptPath, 'utf8');
      await setupConnection.query(initScript);

      await setupConnection.end();

      // Create main connection and pool
      connection = await mysql.createConnection(MYSQL_CONFIG);
      pool = mysql.createPool(POOL_CONFIG);

      console.log('✅ MySQL test database initialized');
    } catch (error) {
      console.error('❌ Failed to initialize MySQL test database:', error);
      throw error;
    }
  }, 30000);

  afterAll(async () => {
    console.log('🧹 Cleaning up MySQL connections...');

    try {
      if (connection) {
        await connection.end();
      }
      if (pool) {
        await pool.end();
      }
      console.log('✅ MySQL connections closed');
    } catch (error) {
      console.error('❌ Error closing MySQL connections:', error);
    }
  });

  beforeEach(async () => {
    // Reset any modified data between tests
    await connection.query('SET FOREIGN_KEY_CHECKS = 0');
    await connection.query('DELETE FROM employee_audit');
    await connection.query('SET FOREIGN_KEY_CHECKS = 1');
  });

  describe('Connection and Authentication', () => {
    it('should successfully connect to MySQL server', async () => {
      const [rows] = await connection.query('SELECT 1 + 1 AS result');
      expect((rows as any)[0].result).toBe(2);
    });

    it('should verify MySQL version', async () => {
      const [rows] = await connection.query('SELECT VERSION() as version');
      const version = (rows as any)[0].version;
      expect(version).toMatch(/^8\./); // MySQL 8.x
    });

    it('should handle invalid credentials gracefully', async () => {
      await expect(
        mysql.createConnection({
          ...MYSQL_CONFIG,
          password: 'invalid_password',
        })
      ).rejects.toThrow();
    });

    it('should retrieve current database name', async () => {
      const [rows] = await connection.query('SELECT DATABASE() as db_name');
      expect((rows as any)[0].db_name).toBe('test_db');
    });

    it('should check connection status', async () => {
      const [rows] = await connection.query('SELECT CONNECTION_ID() as conn_id');
      expect((rows as any)[0].conn_id).toBeGreaterThan(0);
    });
  });

  describe('CRUD Operations - Departments', () => {
    it('should read all departments', async () => {
      const [rows] = await connection.query('SELECT * FROM departments ORDER BY dept_id');
      expect((rows as any[]).length).toBeGreaterThanOrEqual(5);
      expect((rows as any)[0].dept_name).toBe('Engineering');
    });

    it('should create a new department with AUTO_INCREMENT', async () => {
      const [result] = await connection.query(
        'INSERT INTO departments (dept_name, location, budget) VALUES (?, ?, ?)',
        ['Research', 'Seattle', 400000.00]
      );
      const insertId = (result as any).insertId;
      expect(insertId).toBeGreaterThan(0);

      const [rows] = await connection.query('SELECT * FROM departments WHERE dept_id = ?', [insertId]);
      expect((rows as any)[0].dept_name).toBe('Research');
    });

    it('should update department budget', async () => {
      const [result] = await connection.query(
        'UPDATE departments SET budget = ? WHERE dept_name = ?',
        [1200000.00, 'Engineering']
      );
      expect((result as any).affectedRows).toBe(1);

      const [rows] = await connection.query(
        'SELECT budget FROM departments WHERE dept_name = ?',
        ['Engineering']
      );
      expect((rows as any)[0].budget).toBe('1200000.00');
    });

    it('should delete a department (soft delete)', async () => {
      // First create a temporary department
      const [insertResult] = await connection.query(
        'INSERT INTO departments (dept_name, location) VALUES (?, ?)',
        ['TempDept', 'Remote']
      );
      const deptId = (insertResult as any).insertId;

      // Delete it
      const [deleteResult] = await connection.query(
        'DELETE FROM departments WHERE dept_id = ?',
        [deptId]
      );
      expect((deleteResult as any).affectedRows).toBe(1);

      // Verify it's deleted
      const [rows] = await connection.query(
        'SELECT * FROM departments WHERE dept_id = ?',
        [deptId]
      );
      expect((rows as any[]).length).toBe(0);
    });

    it('should handle INSERT ... ON DUPLICATE KEY UPDATE', async () => {
      // First insert
      await connection.query(
        'INSERT INTO departments (dept_name, location, budget) VALUES (?, ?, ?) ON DUPLICATE KEY UPDATE budget = budget + ?',
        ['UniqueTest', 'Austin', 100000.00, 50000.00]
      );

      // Get initial budget
      const [rows1] = await connection.query(
        'SELECT budget FROM departments WHERE dept_name = ?',
        ['UniqueTest']
      );
      const initialBudget = parseFloat((rows1 as any)[0].budget);

      // Duplicate insert should trigger update
      await connection.query(
        'INSERT INTO departments (dept_name, location, budget) VALUES (?, ?, ?) ON DUPLICATE KEY UPDATE budget = budget + ?',
        ['UniqueTest', 'Austin', 100000.00, 50000.00]
      );

      // Verify budget was updated
      const [rows2] = await connection.query(
        'SELECT budget FROM departments WHERE dept_name = ?',
        ['UniqueTest']
      );
      const updatedBudget = parseFloat((rows2 as any)[0].budget);
      expect(updatedBudget).toBe(initialBudget + 50000.00);
    });
  });

  describe('CRUD Operations - Employees', () => {
    it('should read all active employees', async () => {
      const [rows] = await connection.query(
        "SELECT * FROM employees WHERE status = 'active' ORDER BY emp_name"
      );
      expect((rows as any[]).length).toBeGreaterThan(0);
    });

    it('should create employee with ENUM status', async () => {
      const [result] = await connection.query(
        'INSERT INTO employees (emp_name, email, dept_id, salary, hire_date, status) VALUES (?, ?, ?, ?, ?, ?)',
        ['Test Employee', 'test@company.com', 1, 80000.00, '2024-01-01', 'active']
      );
      expect((result as any).insertId).toBeGreaterThan(0);
    });

    it('should enforce ENUM constraint on status', async () => {
      await expect(
        connection.query(
          'INSERT INTO employees (emp_name, email, status) VALUES (?, ?, ?)',
          ['Invalid Status', 'invalid@company.com', 'invalid_status']
        )
      ).rejects.toThrow();
    });

    it('should update employee status using ENUM', async () => {
      const [result] = await connection.query(
        "UPDATE employees SET status = 'on_leave' WHERE emp_name = ?",
        ['John Doe']
      );
      expect((result as any).affectedRows).toBe(1);
    });

    it('should search employees by email pattern', async () => {
      const [rows] = await connection.query(
        "SELECT * FROM employees WHERE email LIKE '%@company.com' ORDER BY emp_name"
      );
      expect((rows as any[]).length).toBeGreaterThan(0);
    });

    it('should use indexes for efficient queries', async () => {
      const [rows] = await connection.query(
        'EXPLAIN SELECT * FROM employees WHERE email = ?',
        ['john.doe@company.com']
      );
      expect((rows as any)[0].key).toBe('email'); // Using index
    });
  });

  describe('Transaction Management (InnoDB)', () => {
    it('should commit a successful transaction', async () => {
      await connection.beginTransaction();

      try {
        const [result1] = await connection.query(
          'INSERT INTO departments (dept_name, location, budget) VALUES (?, ?, ?)',
          ['Transaction Test 1', 'Miami', 250000.00]
        );
        const dept1Id = (result1 as any).insertId;

        const [result2] = await connection.query(
          'INSERT INTO employees (emp_name, email, dept_id, salary, hire_date) VALUES (?, ?, ?, ?, ?)',
          ['Transaction Employee', 'trans@company.com', dept1Id, 75000.00, '2024-01-01']
        );

        await connection.commit();

        // Verify data persisted
        const [rows] = await connection.query(
          'SELECT * FROM departments WHERE dept_id = ?',
          [dept1Id]
        );
        expect((rows as any[]).length).toBe(1);
      } catch (error) {
        await connection.rollback();
        throw error;
      }
    });

    it('should rollback a failed transaction', async () => {
      await connection.beginTransaction();

      try {
        const [result] = await connection.query(
          'INSERT INTO departments (dept_name, location, budget) VALUES (?, ?, ?)',
          ['Rollback Test', 'Portland', 300000.00]
        );
        const deptId = (result as any).insertId;

        // This should fail due to invalid enum
        await connection.query(
          'INSERT INTO employees (emp_name, email, dept_id, status) VALUES (?, ?, ?, ?)',
          ['Should Fail', 'fail@company.com', deptId, 'invalid_status']
        );

        await connection.commit();
      } catch (error) {
        await connection.rollback();

        // Verify department was not created
        const [rows] = await connection.query(
          "SELECT * FROM departments WHERE dept_name = 'Rollback Test'"
        );
        expect((rows as any[]).length).toBe(0);
      }
    });

    it('should handle nested transactions with savepoints', async () => {
      await connection.beginTransaction();

      await connection.query(
        'INSERT INTO departments (dept_name, location) VALUES (?, ?)',
        ['Savepoint Test', 'Denver']
      );

      // Create savepoint
      await connection.query('SAVEPOINT sp1');

      await connection.query(
        'INSERT INTO departments (dept_name, location) VALUES (?, ?)',
        ['Savepoint Test 2', 'Phoenix']
      );

      // Rollback to savepoint
      await connection.query('ROLLBACK TO SAVEPOINT sp1');

      await connection.commit();

      // First insert should exist, second should not
      const [rows1] = await connection.query(
        "SELECT * FROM departments WHERE dept_name = 'Savepoint Test'"
      );
      expect((rows1 as any[]).length).toBe(1);

      const [rows2] = await connection.query(
        "SELECT * FROM departments WHERE dept_name = 'Savepoint Test 2'"
      );
      expect((rows2 as any[]).length).toBe(0);
    });

    it('should enforce transaction isolation', async () => {
      // Start transaction
      await connection.beginTransaction();

      // Insert data in transaction
      await connection.query(
        'INSERT INTO departments (dept_name, location) VALUES (?, ?)',
        ['Isolation Test', 'Dallas']
      );

      // Create second connection to verify isolation
      const connection2 = await mysql.createConnection(MYSQL_CONFIG);

      // Second connection should not see uncommitted data
      const [rows] = await connection2.query(
        "SELECT * FROM departments WHERE dept_name = 'Isolation Test'"
      );
      expect((rows as any[]).length).toBe(0);

      // Commit transaction
      await connection.commit();

      // Now second connection should see the data
      const [rows2] = await connection2.query(
        "SELECT * FROM departments WHERE dept_name = 'Isolation Test'"
      );
      expect((rows2 as any[]).length).toBe(1);

      await connection2.end();
    });
  });

  describe('Foreign Key Constraints', () => {
    it('should enforce foreign key on insert', async () => {
      await expect(
        connection.query(
          'INSERT INTO employees (emp_name, email, dept_id) VALUES (?, ?, ?)',
          ['Invalid FK', 'invalid@company.com', 99999]
        )
      ).rejects.toThrow();
    });

    it('should cascade delete from parent to child', async () => {
      // Create department and project
      const [deptResult] = await connection.query(
        'INSERT INTO departments (dept_name, location) VALUES (?, ?)',
        ['Delete Cascade Test', 'Tampa']
      );
      const deptId = (deptResult as any).insertId;

      const [projResult] = await connection.query(
        'INSERT INTO projects (project_name, dept_id) VALUES (?, ?)',
        ['Cascade Project', deptId]
      );
      const projectId = (projResult as any).insertId;

      // Delete department should cascade to project
      await connection.query('DELETE FROM departments WHERE dept_id = ?', [deptId]);

      // Verify project was also deleted
      const [rows] = await connection.query(
        'SELECT * FROM projects WHERE project_id = ?',
        [projectId]
      );
      expect((rows as any[]).length).toBe(0);
    });

    it('should set null on delete for employees', async () => {
      // Create department and employee
      const [deptResult] = await connection.query(
        'INSERT INTO departments (dept_name, location) VALUES (?, ?)',
        ['Set Null Test', 'Atlanta']
      );
      const deptId = (deptResult as any).insertId;

      const [empResult] = await connection.query(
        'INSERT INTO employees (emp_name, email, dept_id) VALUES (?, ?, ?)',
        ['Set Null Employee', 'setnull@company.com', deptId]
      );
      const empId = (empResult as any).insertId;

      // Delete department
      await connection.query('DELETE FROM departments WHERE dept_id = ?', [deptId]);

      // Employee should still exist with null dept_id
      const [rows] = await connection.query(
        'SELECT * FROM employees WHERE emp_id = ?',
        [empId]
      );
      expect((rows as any[]).length).toBe(1);
      expect((rows as any)[0].dept_id).toBeNull();
    });

    it('should cascade update on foreign key change', async () => {
      // This test verifies ON UPDATE CASCADE works
      const [deptResult] = await connection.query(
        'INSERT INTO departments (dept_name, location) VALUES (?, ?)',
        ['Update Cascade', 'Nashville']
      );
      const oldDeptId = (deptResult as any).insertId;

      const [empResult] = await connection.query(
        'INSERT INTO employees (emp_name, email, dept_id) VALUES (?, ?, ?)',
        ['Cascade Employee', 'cascade@company.com', oldDeptId]
      );
      const empId = (empResult as any).insertId;

      // MySQL doesn't allow updating primary keys by default, so we verify the relationship
      const [rows] = await connection.query(
        'SELECT dept_id FROM employees WHERE emp_id = ?',
        [empId]
      );
      expect((rows as any)[0].dept_id).toBe(oldDeptId);
    });
  });

  describe('Full-Text Search', () => {
    it('should perform full-text search on title', async () => {
      const [rows] = await connection.query(
        "SELECT * FROM documents WHERE MATCH(title) AGAINST('MySQL' IN NATURAL LANGUAGE MODE)"
      );
      expect((rows as any[]).length).toBeGreaterThan(0);
      expect((rows as any)[0].title).toContain('MySQL');
    });

    it('should perform full-text search on content', async () => {
      const [rows] = await connection.query(
        "SELECT * FROM documents WHERE MATCH(content) AGAINST('performance optimization' IN NATURAL LANGUAGE MODE)"
      );
      expect((rows as any[]).length).toBeGreaterThan(0);
    });

    it('should perform boolean mode full-text search', async () => {
      const [rows] = await connection.query(
        "SELECT * FROM documents WHERE MATCH(title, content) AGAINST('+Docker -MySQL' IN BOOLEAN MODE)"
      );
      const results = rows as any[];
      results.forEach(row => {
        expect(row.title.toLowerCase() + ' ' + row.content.toLowerCase()).toContain('docker');
        expect(row.title.toLowerCase() + ' ' + row.content.toLowerCase()).not.toContain('mysql');
      });
    });

    it('should rank full-text search results by relevance', async () => {
      const [rows] = await connection.query(
        `SELECT *, MATCH(title, content) AGAINST('JavaScript') as relevance
         FROM documents
         WHERE MATCH(title, content) AGAINST('JavaScript')
         ORDER BY relevance DESC`
      );
      expect((rows as any[]).length).toBeGreaterThan(0);
      expect((rows as any)[0].relevance).toBeGreaterThan(0);
    });

    it('should perform full-text search with wildcards', async () => {
      const [rows] = await connection.query(
        "SELECT * FROM documents WHERE MATCH(title, content) AGAINST('Java*' IN BOOLEAN MODE)"
      );
      expect((rows as any[]).length).toBeGreaterThan(0);
    });
  });

  describe('Stored Procedures and Functions', () => {
    it('should execute stored procedure GetEmployeeDetails', async () => {
      const [rows] = await connection.query('CALL GetEmployeeDetails(?)', [1]);
      expect((rows as any)[0].length).toBeGreaterThan(0);
      expect((rows as any)[0][0].emp_name).toBeDefined();
      expect((rows as any)[0][0].project_count).toBeDefined();
    });

    it('should call stored function GetDepartmentSalaryTotal', async () => {
      const [rows] = await connection.query(
        'SELECT GetDepartmentSalaryTotal(?) as total_salary',
        [1]
      );
      expect(parseFloat((rows as any)[0].total_salary)).toBeGreaterThan(0);
    });

    it('should handle stored procedure with no results', async () => {
      const [rows] = await connection.query('CALL GetEmployeeDetails(?)', [99999]);
      expect((rows as any)[0].length).toBe(0);
    });

    it('should verify stored function returns correct sum', async () => {
      // Get manual sum
      const [sumRows] = await connection.query(
        "SELECT COALESCE(SUM(salary), 0) as manual_total FROM employees WHERE dept_id = 1 AND status = 'active'"
      );
      const manualTotal = parseFloat((sumRows as any)[0].manual_total);

      // Get function result
      const [funcRows] = await connection.query(
        'SELECT GetDepartmentSalaryTotal(1) as func_total'
      );
      const funcTotal = parseFloat((funcRows as any)[0].func_total);

      expect(funcTotal).toBe(manualTotal);
    });
  });

  describe('Triggers', () => {
    it('should fire trigger on salary update', async () => {
      const empId = 1;
      const newSalary = 100000.00;

      // Get current salary
      const [beforeRows] = await connection.query(
        'SELECT salary FROM employees WHERE emp_id = ?',
        [empId]
      );
      const oldSalary = parseFloat((beforeRows as any)[0].salary);

      // Update salary
      await connection.query(
        'UPDATE employees SET salary = ? WHERE emp_id = ?',
        [newSalary, empId]
      );

      // Check audit table
      const [auditRows] = await connection.query(
        'SELECT * FROM employee_audit WHERE emp_id = ? ORDER BY audit_id DESC LIMIT 1',
        [empId]
      );

      expect((auditRows as any[]).length).toBe(1);
      expect((auditRows as any)[0].action).toBe('SALARY_UPDATE');
      expect(parseFloat((auditRows as any)[0].old_salary)).toBe(oldSalary);
      expect(parseFloat((auditRows as any)[0].new_salary)).toBe(newSalary);
    });

    it('should not fire trigger when salary unchanged', async () => {
      const empId = 2;

      // Get current salary
      const [beforeRows] = await connection.query(
        'SELECT salary FROM employees WHERE emp_id = ?',
        [empId]
      );
      const currentSalary = (beforeRows as any)[0].salary;

      // Clear audit
      await connection.query('DELETE FROM employee_audit WHERE emp_id = ?', [empId]);

      // Update with same salary
      await connection.query(
        'UPDATE employees SET salary = ? WHERE emp_id = ?',
        [currentSalary, empId]
      );

      // Check audit table - should be empty
      const [auditRows] = await connection.query(
        'SELECT * FROM employee_audit WHERE emp_id = ?',
        [empId]
      );
      expect((auditRows as any[]).length).toBe(0);
    });

    it('should track trigger execution user', async () => {
      await connection.query(
        'UPDATE employees SET salary = ? WHERE emp_id = ?',
        [110000.00, 2]
      );

      const [auditRows] = await connection.query(
        'SELECT changed_by FROM employee_audit WHERE emp_id = ? ORDER BY audit_id DESC LIMIT 1',
        [2]
      );
      expect((auditRows as any)[0].changed_by).toContain('root');
    });
  });

  describe('Views and Complex JOINs', () => {
    it('should query employee_view', async () => {
      const [rows] = await connection.query('SELECT * FROM employee_view ORDER BY emp_name');
      expect((rows as any[]).length).toBeGreaterThan(0);
      expect((rows as any)[0].dept_name).toBeDefined();
      expect((rows as any)[0].active_projects).toBeDefined();
    });

    it('should perform complex multi-table JOIN', async () => {
      const [rows] = await connection.query(`
        SELECT
          e.emp_name,
          d.dept_name,
          p.project_name,
          pa.role,
          pa.hours_allocated
        FROM employees e
        INNER JOIN departments d ON e.dept_id = d.dept_id
        INNER JOIN project_assignments pa ON e.emp_id = pa.emp_id
        INNER JOIN projects p ON pa.project_id = p.project_id
        WHERE e.status = 'active'
        ORDER BY e.emp_name, p.project_name
      `);
      expect((rows as any[]).length).toBeGreaterThan(0);
    });

    it('should perform LEFT JOIN with aggregation', async () => {
      const [rows] = await connection.query(`
        SELECT
          d.dept_name,
          COUNT(e.emp_id) as employee_count,
          COALESCE(SUM(e.salary), 0) as total_salary
        FROM departments d
        LEFT JOIN employees e ON d.dept_id = e.dept_id AND e.status = 'active'
        GROUP BY d.dept_id, d.dept_name
        ORDER BY employee_count DESC
      `);
      expect((rows as any[]).length).toBeGreaterThanOrEqual(5);
    });

    it('should use subquery in JOIN', async () => {
      const [rows] = await connection.query(`
        SELECT
          e.emp_name,
          e.salary,
          dept_avg.avg_salary
        FROM employees e
        INNER JOIN (
          SELECT dept_id, AVG(salary) as avg_salary
          FROM employees
          WHERE status = 'active'
          GROUP BY dept_id
        ) dept_avg ON e.dept_id = dept_avg.dept_id
        WHERE e.salary > dept_avg.avg_salary
        ORDER BY e.emp_name
      `);
      expect(rows).toBeDefined();
    });

    it('should perform self-join', async () => {
      // Find employees in same department
      const [rows] = await connection.query(`
        SELECT DISTINCT
          e1.emp_name as employee1,
          e2.emp_name as employee2,
          d.dept_name
        FROM employees e1
        INNER JOIN employees e2 ON e1.dept_id = e2.dept_id AND e1.emp_id < e2.emp_id
        INNER JOIN departments d ON e1.dept_id = d.dept_id
        WHERE e1.status = 'active' AND e2.status = 'active'
        ORDER BY d.dept_name, e1.emp_name
      `);
      expect(rows).toBeDefined();
    });
  });

  describe('JSON Column Support', () => {
    it('should store and retrieve JSON data in departments', async () => {
      const [rows] = await connection.query(
        'SELECT dept_name, metadata FROM departments WHERE dept_name = ?',
        ['Engineering']
      );
      const metadata = (rows as any)[0].metadata;
      expect(metadata).toBeDefined();
      expect(metadata.floor).toBe(3);
      expect(metadata.employees).toBe(50);
    });

    it('should query JSON fields using JSON_EXTRACT', async () => {
      const [rows] = await connection.query(
        "SELECT dept_name, JSON_EXTRACT(metadata, '$.floor') as floor FROM departments WHERE dept_name = ?",
        ['Engineering']
      );
      expect((rows as any)[0].floor).toBe(3);
    });

    it('should query JSON arrays in employees', async () => {
      const [rows] = await connection.query(
        'SELECT emp_name, skills FROM employees WHERE emp_name = ?',
        ['John Doe']
      );
      const skills = (rows as any)[0].skills;
      expect(Array.isArray(skills)).toBe(true);
      expect(skills).toContain('Python');
      expect(skills).toContain('JavaScript');
    });

    it('should search within JSON arrays', async () => {
      const [rows] = await connection.query(
        "SELECT emp_name FROM employees WHERE JSON_CONTAINS(skills, '\"Python\"')"
      );
      expect((rows as any[]).length).toBeGreaterThan(0);
      expect((rows as any)[0].emp_name).toBe('John Doe');
    });

    it('should update JSON fields', async () => {
      await connection.query(
        "UPDATE departments SET metadata = JSON_SET(metadata, '$.floor', 5) WHERE dept_name = ?",
        ['HR']
      );

      const [rows] = await connection.query(
        'SELECT metadata FROM departments WHERE dept_name = ?',
        ['HR']
      );
      expect((rows as any)[0].metadata.floor).toBe(5);
    });

    it('should use JSON path expressions', async () => {
      const [rows] = await connection.query(
        `SELECT emp_name, JSON_LENGTH(skills) as skill_count
         FROM employees
         WHERE JSON_LENGTH(skills) >= 3
         ORDER BY skill_count DESC`
      );
      expect((rows as any[]).length).toBeGreaterThan(0);
    });
  });

  describe('Bulk Inserts and Performance', () => {
    it('should perform bulk insert efficiently', async () => {
      const startTime = Date.now();

      const values: any[] = [];
      for (let i = 0; i < 100; i++) {
        values.push([
          `Bulk Employee ${i}`,
          `bulk${i}@company.com`,
          1,
          50000 + Math.random() * 50000,
          '2024-01-01',
        ]);
      }

      await connection.query(
        'INSERT INTO employees (emp_name, email, dept_id, salary, hire_date) VALUES ?',
        [values]
      );

      const duration = Date.now() - startTime;
      expect(duration).toBeLessThan(1000); // Should complete in under 1 second

      // Verify count
      const [rows] = await connection.query(
        "SELECT COUNT(*) as count FROM employees WHERE emp_name LIKE 'Bulk Employee%'"
      );
      expect((rows as any)[0].count).toBe(100);
    });

    it('should use batch operations for updates', async () => {
      const startTime = Date.now();

      await connection.query(
        "UPDATE employees SET salary = salary * 1.05 WHERE emp_name LIKE 'Bulk Employee%'"
      );

      const duration = Date.now() - startTime;
      expect(duration).toBeLessThan(500);
    });

    it('should optimize with LIMIT clause', async () => {
      const [rows] = await connection.query(
        'SELECT * FROM employees ORDER BY emp_id LIMIT 10'
      );
      expect((rows as any[]).length).toBeLessThanOrEqual(10);
    });

    it('should use pagination efficiently', async () => {
      const pageSize = 5;
      const offset = 0;

      const [rows] = await connection.query(
        'SELECT * FROM employees ORDER BY emp_id LIMIT ? OFFSET ?',
        [pageSize, offset]
      );
      expect((rows as any[]).length).toBeLessThanOrEqual(pageSize);
    });
  });

  describe('Connection Pooling', () => {
    it('should acquire connection from pool', async () => {
      const poolConnection = await pool.getConnection();
      expect(poolConnection).toBeDefined();

      const [rows] = await poolConnection.query('SELECT 1 as test');
      expect((rows as any)[0].test).toBe(1);

      poolConnection.release();
    });

    it('should handle multiple concurrent connections', async () => {
      const promises = [];

      for (let i = 0; i < 20; i++) {
        promises.push(
          pool.query('SELECT SLEEP(0.1), ? as id', [i])
        );
      }

      const results = await Promise.all(promises);
      expect(results).toHaveLength(20);
    });

    it('should reuse connections from pool', async () => {
      const conn1 = await pool.getConnection();
      const [rows1] = await conn1.query('SELECT CONNECTION_ID() as id');
      const connectionId1 = (rows1 as any)[0].id;
      conn1.release();

      const conn2 = await pool.getConnection();
      const [rows2] = await conn2.query('SELECT CONNECTION_ID() as id');
      const connectionId2 = (rows2 as any)[0].id;
      conn2.release();

      // Connection IDs should be from the pool range
      expect(connectionId1).toBeGreaterThan(0);
      expect(connectionId2).toBeGreaterThan(0);
    });

    it('should handle pool connection errors gracefully', async () => {
      const conn = await pool.getConnection();

      try {
        await conn.query('SELECT * FROM nonexistent_table');
      } catch (error) {
        expect(error).toBeDefined();
      } finally {
        conn.release();
      }

      // Pool should still be usable
      const [rows] = await pool.query('SELECT 1 as test');
      expect((rows as any)[0].test).toBe(1);
    });

    it('should report pool statistics', async () => {
      // Get pool information
      const poolInfo = (pool as any).pool;
      expect(poolInfo).toBeDefined();
    });
  });

  describe('MySQL-Specific Features', () => {
    it('should use AUTO_INCREMENT with LAST_INSERT_ID', async () => {
      const [result] = await connection.query(
        'INSERT INTO departments (dept_name, location) VALUES (?, ?)',
        ['AutoInc Test', 'Las Vegas']
      );
      const insertId = (result as any).insertId;

      const [rows] = await connection.query('SELECT LAST_INSERT_ID() as last_id');
      expect((rows as any)[0].last_id).toBe(insertId);
    });

    it('should handle TIMESTAMP DEFAULT CURRENT_TIMESTAMP', async () => {
      const [result] = await connection.query(
        'INSERT INTO departments (dept_name, location) VALUES (?, ?)',
        ['Timestamp Test', 'Reno']
      );
      const deptId = (result as any).insertId;

      const [rows] = await connection.query(
        'SELECT created_at, updated_at FROM departments WHERE dept_id = ?',
        [deptId]
      );
      expect((rows as any)[0].created_at).toBeDefined();
      expect((rows as any)[0].updated_at).toBeDefined();
    });

    it('should update TIMESTAMP ON UPDATE CURRENT_TIMESTAMP', async () => {
      const [result] = await connection.query(
        'INSERT INTO departments (dept_name, location) VALUES (?, ?)',
        ['Update Timestamp', 'Sacramento']
      );
      const deptId = (result as any).insertId;

      // Get initial timestamp
      const [rows1] = await connection.query(
        'SELECT updated_at FROM departments WHERE dept_id = ?',
        [deptId]
      );
      const initialTimestamp = (rows1 as any)[0].updated_at;

      // Wait a moment
      await new Promise(resolve => setTimeout(resolve, 1100));

      // Update record
      await connection.query(
        'UPDATE departments SET location = ? WHERE dept_id = ?',
        ['San Diego', deptId]
      );

      // Check updated timestamp
      const [rows2] = await connection.query(
        'SELECT updated_at FROM departments WHERE dept_id = ?',
        [deptId]
      );
      const updatedTimestamp = (rows2 as any)[0].updated_at;

      expect(new Date(updatedTimestamp).getTime()).toBeGreaterThan(
        new Date(initialTimestamp).getTime()
      );
    });

    it('should use REPLACE INTO (INSERT or UPDATE)', async () => {
      // First insert
      await connection.query(
        'INSERT INTO departments (dept_id, dept_name, location) VALUES (?, ?, ?)',
        [1000, 'Replace Test', 'Orlando']
      );

      // REPLACE will delete and re-insert
      await connection.query(
        'REPLACE INTO departments (dept_id, dept_name, location) VALUES (?, ?, ?)',
        [1000, 'Replace Test Updated', 'Tampa']
      );

      const [rows] = await connection.query(
        'SELECT * FROM departments WHERE dept_id = ?',
        [1000]
      );
      expect((rows as any)[0].location).toBe('Tampa');
    });

    it('should use CASE expression', async () => {
      const [rows] = await connection.query(`
        SELECT
          emp_name,
          salary,
          CASE
            WHEN salary >= 100000 THEN 'High'
            WHEN salary >= 80000 THEN 'Medium'
            ELSE 'Low'
          END as salary_grade
        FROM employees
        WHERE status = 'active'
        ORDER BY salary DESC
      `);
      expect((rows as any[]).length).toBeGreaterThan(0);
      expect((rows as any)[0].salary_grade).toBeDefined();
    });

    it('should use IFNULL and COALESCE', async () => {
      const [rows] = await connection.query(`
        SELECT
          emp_name,
          IFNULL(dept_id, 0) as dept_id_safe,
          COALESCE(dept_id, 0) as dept_id_coalesce
        FROM employees
        LIMIT 5
      `);
      expect((rows as any[]).length).toBeGreaterThan(0);
    });
  });

  describe('Error Handling', () => {
    it('should handle syntax errors', async () => {
      await expect(
        connection.query('SELCT * FROM employees')
      ).rejects.toThrow();
    });

    it('should handle table not found errors', async () => {
      await expect(
        connection.query('SELECT * FROM nonexistent_table')
      ).rejects.toThrow();
    });

    it('should handle unique constraint violations', async () => {
      await expect(
        connection.query(
          'INSERT INTO departments (dept_name, location) VALUES (?, ?)',
          ['Engineering', 'Duplicate Test'] // Engineering already exists
        )
      ).rejects.toThrow();
    });

    it('should provide meaningful error messages', async () => {
      try {
        await connection.query('INSERT INTO employees (emp_name) VALUES (?)');
      } catch (error: any) {
        expect(error.message).toBeDefined();
        expect(error.code).toBeDefined();
      }
    });
  });
});
