/**
 * Oracle Database Integration Tests
 *
 * Comprehensive integration tests for Oracle database client using Docker test environment.
 * Tests both CDB$ROOT and FREEPDB1 pluggable database.
 *
 * Prerequisites:
 * - Oracle database running on localhost:1521
 * - Test data initialized from init-oracle.sql
 *
 * Connection Details:
 * - CDB$ROOT: localhost:1521/free, SYS as SYSDBA, MyOraclePass123
 * - FREEPDB1: localhost:1521/freepdb1, SYS as SYSDBA, MyOraclePass123
 */

import { describe, it, expect, beforeAll, afterAll, beforeEach, afterEach } from 'vitest';
import oracledb from 'oracledb';

// Oracle connection configuration
interface OracleConfig {
  user: string;
  password: string;
  connectString: string;
  privilege?: number;
}

// Test result interface
interface QueryResult {
  rows: any[];
  metaData?: any[];
  rowsAffected?: number;
}

// Oracle client wrapper for testing
class OracleTestClient {
  private connection: oracledb.Connection | null = null;
  private config: OracleConfig;

  constructor(config: OracleConfig) {
    this.config = config;
  }

  async connect(): Promise<void> {
    try {
      this.connection = await oracledb.getConnection(this.config);
    } catch (error) {
      throw new Error(`Failed to connect to Oracle: ${error}`);
    }
  }

  async disconnect(): Promise<void> {
    if (this.connection) {
      await this.connection.close();
      this.connection = null;
    }
  }

  async execute(sql: string, binds: any = [], options: any = {}): Promise<QueryResult> {
    if (!this.connection) {
      throw new Error('Not connected to database');
    }

    try {
      const result = await this.connection.execute(sql, binds, {
        autoCommit: true,
        outFormat: oracledb.OUT_FORMAT_OBJECT,
        ...options
      });

      return {
        rows: result.rows || [],
        metaData: result.metaData,
        rowsAffected: result.rowsAffected
      };
    } catch (error) {
      throw new Error(`Query execution failed: ${error}`);
    }
  }

  async executeMany(sql: string, binds: any[]): Promise<QueryResult> {
    if (!this.connection) {
      throw new Error('Not connected to database');
    }

    const result = await this.connection.executeMany(sql, binds, {
      autoCommit: true
    });

    return {
      rows: [],
      rowsAffected: result.rowsAffected
    };
  }

  async commit(): Promise<void> {
    if (this.connection) {
      await this.connection.commit();
    }
  }

  async rollback(): Promise<void> {
    if (this.connection) {
      await this.connection.rollback();
    }
  }

  isConnected(): boolean {
    return this.connection !== null;
  }
}

// Test configurations
const CDB_CONFIG: OracleConfig = {
  user: 'SYS',
  password: 'MyOraclePass123',
  connectString: 'localhost:1521/FREE',
  privilege: oracledb.SYSDBA
};

const PDB_CONFIG: OracleConfig = {
  user: 'SYS',
  password: 'MyOraclePass123',
  connectString: 'localhost:1521/FREEPDB1',
  privilege: oracledb.SYSDBA
};

describe('Oracle CDB$ROOT Integration Tests', () => {
  let client: OracleTestClient;

  beforeAll(async () => {
    // Initialize Oracle client library
    oracledb.outFormat = oracledb.OUT_FORMAT_OBJECT;
  });

  beforeEach(async () => {
    client = new OracleTestClient(CDB_CONFIG);
    await client.connect();
  });

  afterEach(async () => {
    await client.disconnect();
  });

  describe('Connection Management', () => {
    it('should successfully connect to CDB$ROOT', async () => {
      expect(client.isConnected()).toBe(true);
    });

    it('should execute simple DUAL query', async () => {
      const result = await client.execute('SELECT 1 AS num FROM DUAL');

      expect(result.rows).toHaveLength(1);
      expect(result.rows[0].NUM).toBe(1);
    });

    it('should retrieve Oracle version', async () => {
      const result = await client.execute(
        'SELECT banner FROM v$version WHERE ROWNUM = 1'
      );

      expect(result.rows).toHaveLength(1);
      expect(result.rows[0].BANNER).toContain('Oracle');
    });

    it('should get database name', async () => {
      const result = await client.execute('SELECT name FROM v$database');

      expect(result.rows).toHaveLength(1);
      expect(['FREE', 'XE', 'ORCL']).toContain(result.rows[0].NAME);
    });

    it('should verify connection as SYS user', async () => {
      const result = await client.execute('SELECT USER FROM DUAL');

      expect(result.rows[0].USER).toBe('SYS');
    });
  });

  describe('Basic Queries', () => {
    it('should execute SYSDATE query', async () => {
      const result = await client.execute('SELECT SYSDATE AS current_date FROM DUAL');

      expect(result.rows).toHaveLength(1);
      expect(result.rows[0].CURRENT_DATE).toBeInstanceOf(Date);
    });

    it('should execute numeric operations', async () => {
      const result = await client.execute(`
        SELECT
          10 + 5 AS addition,
          10 - 5 AS subtraction,
          10 * 5 AS multiplication,
          10 / 5 AS division
        FROM DUAL
      `);

      expect(result.rows[0].ADDITION).toBe(15);
      expect(result.rows[0].SUBTRACTION).toBe(5);
      expect(result.rows[0].MULTIPLICATION).toBe(50);
      expect(result.rows[0].DIVISION).toBe(2);
    });

    it('should execute string operations', async () => {
      const result = await client.execute(`
        SELECT
          UPPER('oracle') AS upper_case,
          LOWER('ORACLE') AS lower_case,
          LENGTH('Oracle') AS str_length,
          'Hello' || ' ' || 'World' AS concatenated
        FROM DUAL
      `);

      expect(result.rows[0].UPPER_CASE).toBe('ORACLE');
      expect(result.rows[0].LOWER_CASE).toBe('oracle');
      expect(result.rows[0].STR_LENGTH).toBe(6);
      expect(result.rows[0].CONCATENATED).toBe('Hello World');
    });
  });
});

describe('Oracle FREEPDB1 Integration Tests', () => {
  let client: OracleTestClient;

  beforeEach(async () => {
    client = new OracleTestClient(PDB_CONFIG);
    await client.connect();
  });

  afterEach(async () => {
    await client.disconnect();
  });

  describe('Connection to PDB', () => {
    it('should connect to FREEPDB1', async () => {
      expect(client.isConnected()).toBe(true);
    });

    it('should verify container info', async () => {
      const result = await client.execute(`
        SELECT con_id, name
        FROM v$containers
        WHERE name = 'FREEPDB1'
      `);

      expect(result.rows.length).toBeGreaterThan(0);
    });
  });

  describe('CRUD Operations', () => {
    const TEST_TABLE = 'test_crud_operations';

    beforeEach(async () => {
      // Create test table
      await client.execute(`
        BEGIN
          EXECUTE IMMEDIATE 'DROP TABLE ${TEST_TABLE}';
        EXCEPTION
          WHEN OTHERS THEN NULL;
        END;
      `);

      await client.execute(`
        CREATE TABLE ${TEST_TABLE} (
          id NUMBER PRIMARY KEY,
          name VARCHAR2(100),
          email VARCHAR2(255),
          age NUMBER,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
      `);
    });

    afterEach(async () => {
      await client.execute(`DROP TABLE ${TEST_TABLE}`);
    });

    it('should INSERT data', async () => {
      const result = await client.execute(`
        INSERT INTO ${TEST_TABLE} (id, name, email, age)
        VALUES (1, 'John Doe', 'john@example.com', 30)
      `);

      expect(result.rowsAffected).toBe(1);
    });

    it('should INSERT with bind parameters', async () => {
      const result = await client.execute(
        `INSERT INTO ${TEST_TABLE} (id, name, email, age) VALUES (:id, :name, :email, :age)`,
        {
          id: 2,
          name: 'Jane Smith',
          email: 'jane@example.com',
          age: 28
        }
      );

      expect(result.rowsAffected).toBe(1);
    });

    it('should SELECT inserted data', async () => {
      await client.execute(
        `INSERT INTO ${TEST_TABLE} (id, name, email, age) VALUES (:id, :name, :email, :age)`,
        { id: 3, name: 'Bob Johnson', email: 'bob@example.com', age: 35 }
      );

      const result = await client.execute(
        `SELECT * FROM ${TEST_TABLE} WHERE id = :id`,
        { id: 3 }
      );

      expect(result.rows).toHaveLength(1);
      expect(result.rows[0].NAME).toBe('Bob Johnson');
      expect(result.rows[0].EMAIL).toBe('bob@example.com');
      expect(result.rows[0].AGE).toBe(35);
    });

    it('should UPDATE data', async () => {
      await client.execute(
        `INSERT INTO ${TEST_TABLE} (id, name, email, age) VALUES (4, 'Alice', 'alice@example.com', 25)`
      );

      const updateResult = await client.execute(
        `UPDATE ${TEST_TABLE} SET age = :age WHERE id = :id`,
        { age: 26, id: 4 }
      );

      expect(updateResult.rowsAffected).toBe(1);

      const selectResult = await client.execute(
        `SELECT age FROM ${TEST_TABLE} WHERE id = 4`
      );

      expect(selectResult.rows[0].AGE).toBe(26);
    });

    it('should DELETE data', async () => {
      await client.execute(
        `INSERT INTO ${TEST_TABLE} (id, name, email, age) VALUES (5, 'Charlie', 'charlie@example.com', 40)`
      );

      const deleteResult = await client.execute(
        `DELETE FROM ${TEST_TABLE} WHERE id = :id`,
        { id: 5 }
      );

      expect(deleteResult.rowsAffected).toBe(1);

      const selectResult = await client.execute(
        `SELECT COUNT(*) AS cnt FROM ${TEST_TABLE} WHERE id = 5`
      );

      expect(selectResult.rows[0].CNT).toBe(0);
    });

    it('should handle bulk INSERT', async () => {
      const records = [
        { id: 10, name: 'User10', email: 'user10@example.com', age: 20 },
        { id: 11, name: 'User11', email: 'user11@example.com', age: 21 },
        { id: 12, name: 'User12', email: 'user12@example.com', age: 22 },
        { id: 13, name: 'User13', email: 'user13@example.com', age: 23 },
        { id: 14, name: 'User14', email: 'user14@example.com', age: 24 }
      ];

      const binds = records.map(r => [r.id, r.name, r.email, r.age]);

      const result = await client.executeMany(
        `INSERT INTO ${TEST_TABLE} (id, name, email, age) VALUES (:1, :2, :3, :4)`,
        binds
      );

      expect(result.rowsAffected).toBe(5);

      const selectResult = await client.execute(
        `SELECT COUNT(*) AS cnt FROM ${TEST_TABLE}`
      );

      expect(selectResult.rows[0].CNT).toBe(5);
    });
  });

  describe('Transaction Management', () => {
    const TEST_TABLE = 'test_transactions';

    beforeEach(async () => {
      await client.execute(`
        BEGIN
          EXECUTE IMMEDIATE 'DROP TABLE ${TEST_TABLE}';
        EXCEPTION
          WHEN OTHERS THEN NULL;
        END;
      `);

      await client.execute(`
        CREATE TABLE ${TEST_TABLE} (
          id NUMBER PRIMARY KEY,
          value VARCHAR2(100)
        )
      `);
    });

    afterEach(async () => {
      await client.execute(`DROP TABLE ${TEST_TABLE}`);
    });

    it('should COMMIT transaction', async () => {
      await client.execute(
        `INSERT INTO ${TEST_TABLE} (id, value) VALUES (1, 'committed')`,
        [],
        { autoCommit: false }
      );

      await client.commit();

      const result = await client.execute(
        `SELECT * FROM ${TEST_TABLE} WHERE id = 1`
      );

      expect(result.rows).toHaveLength(1);
      expect(result.rows[0].VALUE).toBe('committed');
    });

    it('should ROLLBACK transaction', async () => {
      await client.execute(
        `INSERT INTO ${TEST_TABLE} (id, value) VALUES (2, 'will_rollback')`,
        [],
        { autoCommit: false }
      );

      await client.rollback();

      const result = await client.execute(
        `SELECT COUNT(*) AS cnt FROM ${TEST_TABLE} WHERE id = 2`
      );

      expect(result.rows[0].CNT).toBe(0);
    });

    it('should handle multiple operations in transaction', async () => {
      await client.execute(
        `INSERT INTO ${TEST_TABLE} (id, value) VALUES (3, 'first')`,
        [],
        { autoCommit: false }
      );

      await client.execute(
        `INSERT INTO ${TEST_TABLE} (id, value) VALUES (4, 'second')`,
        [],
        { autoCommit: false }
      );

      await client.execute(
        `UPDATE ${TEST_TABLE} SET value = 'updated' WHERE id = 3`,
        [],
        { autoCommit: false }
      );

      await client.commit();

      const result = await client.execute(
        `SELECT * FROM ${TEST_TABLE} ORDER BY id`
      );

      expect(result.rows).toHaveLength(2);
      expect(result.rows[0].VALUE).toBe('updated');
      expect(result.rows[1].VALUE).toBe('second');
    });
  });

  describe('Stored Procedures and Functions', () => {
    beforeAll(async () => {
      const adminClient = new OracleTestClient(PDB_CONFIG);
      await adminClient.connect();

      // Create test procedure
      await adminClient.execute(`
        CREATE OR REPLACE PROCEDURE test_proc_add(
          p_num1 IN NUMBER,
          p_num2 IN NUMBER,
          p_result OUT NUMBER
        )
        AS
        BEGIN
          p_result := p_num1 + p_num2;
        END;
      `);

      // Create test function
      await adminClient.execute(`
        CREATE OR REPLACE FUNCTION test_func_multiply(
          p_num1 IN NUMBER,
          p_num2 IN NUMBER
        )
        RETURN NUMBER
        AS
        BEGIN
          RETURN p_num1 * p_num2;
        END;
      `);

      await adminClient.disconnect();
    });

    it('should call stored procedure', async () => {
      const result = await client.execute(
        `BEGIN test_proc_add(:num1, :num2, :result); END;`,
        {
          num1: 10,
          num2: 20,
          result: { dir: oracledb.BIND_OUT, type: oracledb.NUMBER }
        }
      );

      expect((result as any).outBinds?.result).toBe(30);
    });

    it('should call function in SELECT', async () => {
      const result = await client.execute(
        `SELECT test_func_multiply(5, 6) AS product FROM DUAL`
      );

      expect(result.rows[0].PRODUCT).toBe(30);
    });
  });

  describe('Sequences and Triggers', () => {
    const TEST_SEQ = 'test_sequence';
    const TEST_TABLE = 'test_auto_increment';

    beforeEach(async () => {
      // Clean up
      await client.execute(`
        BEGIN
          EXECUTE IMMEDIATE 'DROP SEQUENCE test_user.${TEST_SEQ}';
        EXCEPTION
          WHEN OTHERS THEN NULL;
        END;
      `);

      await client.execute(`
        BEGIN
          EXECUTE IMMEDIATE 'DROP TABLE test_user.${TEST_TABLE}';
        EXCEPTION
          WHEN OTHERS THEN NULL;
        END;
      `);

      // Create sequence in test_user schema
      await client.execute(`CREATE SEQUENCE test_user.${TEST_SEQ} START WITH 100 INCREMENT BY 1`);

      // Create table with trigger in test_user schema
      await client.execute(`
        CREATE TABLE test_user.${TEST_TABLE} (
          id NUMBER PRIMARY KEY,
          name VARCHAR2(100)
        )
      `);

      await client.execute(`
        CREATE OR REPLACE TRIGGER test_user.trg_${TEST_TABLE}
          BEFORE INSERT ON test_user.${TEST_TABLE}
          FOR EACH ROW
          WHEN (NEW.id IS NULL)
        BEGIN
          SELECT test_user.${TEST_SEQ}.NEXTVAL INTO :NEW.id FROM DUAL;
        END;
      `);
    });

    afterEach(async () => {
      await client.execute(`DROP TABLE test_user.${TEST_TABLE}`);
      await client.execute(`DROP SEQUENCE test_user.${TEST_SEQ}`);
    });

    it('should use sequence manually', async () => {
      const result = await client.execute(`SELECT test_user.${TEST_SEQ}.NEXTVAL AS next_val FROM DUAL`);

      expect(result.rows[0].NEXT_VAL).toBeGreaterThanOrEqual(100);
    });

    it('should auto-populate ID with trigger', async () => {
      await client.execute(
        `INSERT INTO test_user.${TEST_TABLE} (name) VALUES ('Auto ID')`
      );

      const result = await client.execute(
        `SELECT id, name FROM test_user.${TEST_TABLE} WHERE name = 'Auto ID'`
      );

      expect(result.rows).toHaveLength(1);
      expect(result.rows[0].ID).toBeGreaterThanOrEqual(100);
    });
  });

  describe('Complex Queries', () => {
    it('should execute JOIN query', async () => {
      const result = await client.execute(`
        SELECT
          e.employee_id,
          e.first_name || ' ' || e.last_name AS full_name,
          d.department_name
        FROM test_user.employees e
        INNER JOIN test_user.departments d ON e.department_id = d.department_id
        WHERE e.is_active = 1
        ORDER BY e.employee_id
      `);

      expect(result.rows.length).toBeGreaterThan(0);
      result.rows.forEach(row => {
        expect(row).toHaveProperty('EMPLOYEE_ID');
        expect(row).toHaveProperty('FULL_NAME');
        expect(row).toHaveProperty('DEPARTMENT_NAME');
      });
    });

    it('should execute subquery', async () => {
      const result = await client.execute(`
        SELECT
          department_name,
          (SELECT COUNT(*)
           FROM test_user.employees e
           WHERE e.department_id = d.department_id
           AND e.is_active = 1) AS employee_count
        FROM test_user.departments d
        ORDER BY department_name
      `);

      expect(result.rows.length).toBeGreaterThan(0);
      result.rows.forEach(row => {
        expect(row).toHaveProperty('DEPARTMENT_NAME');
        expect(row).toHaveProperty('EMPLOYEE_COUNT');
        expect(typeof row.EMPLOYEE_COUNT).toBe('number');
      });
    });

    it('should execute CTE (Common Table Expression)', async () => {
      const result = await client.execute(`
        WITH dept_stats AS (
          SELECT
            department_id,
            COUNT(*) AS emp_count,
            AVG(salary) AS avg_salary
          FROM test_user.employees
          WHERE is_active = 1
          GROUP BY department_id
        )
        SELECT
          d.department_name,
          ds.emp_count,
          ROUND(ds.avg_salary, 2) AS avg_salary
        FROM dept_stats ds
        JOIN test_user.departments d ON ds.department_id = d.department_id
        ORDER BY ds.emp_count DESC
      `);

      expect(result.rows.length).toBeGreaterThan(0);
    });

    it('should execute aggregation query', async () => {
      const result = await client.execute(`
        SELECT
          d.department_name,
          COUNT(e.employee_id) AS total_employees,
          MIN(e.salary) AS min_salary,
          MAX(e.salary) AS max_salary,
          AVG(e.salary) AS avg_salary,
          SUM(e.salary) AS total_salary
        FROM test_user.departments d
        LEFT JOIN test_user.employees e ON d.department_id = e.department_id
        WHERE e.is_active = 1
        GROUP BY d.department_name
        HAVING COUNT(e.employee_id) > 0
        ORDER BY total_employees DESC
      `);

      expect(result.rows.length).toBeGreaterThan(0);
      result.rows.forEach(row => {
        expect(row.TOTAL_EMPLOYEES).toBeGreaterThan(0);
        expect(row.AVG_SALARY).toBeGreaterThan(0);
      });
    });
  });

  describe('Bulk Operations', () => {
    const TEST_TABLE = 'test_bulk_ops';

    beforeEach(async () => {
      await client.execute(`
        BEGIN
          EXECUTE IMMEDIATE 'DROP TABLE ${TEST_TABLE}';
        EXCEPTION
          WHEN OTHERS THEN NULL;
        END;
      `);

      await client.execute(`
        CREATE TABLE ${TEST_TABLE} (
          id NUMBER PRIMARY KEY,
          data VARCHAR2(100),
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
      `);
    });

    afterEach(async () => {
      await client.execute(`DROP TABLE ${TEST_TABLE}`);
    });

    it('should handle bulk insert of 100 rows', async () => {
      const binds = Array.from({ length: 100 }, (_, i) => [
        i + 1,
        `Data ${i + 1}`
      ]);

      const result = await client.executeMany(
        `INSERT INTO ${TEST_TABLE} (id, data) VALUES (:1, :2)`,
        binds
      );

      expect(result.rowsAffected).toBe(100);

      const countResult = await client.execute(
        `SELECT COUNT(*) AS cnt FROM ${TEST_TABLE}`
      );

      expect(countResult.rows[0].CNT).toBe(100);
    });

    it('should handle bulk update', async () => {
      // Insert initial data
      const insertBinds = Array.from({ length: 50 }, (_, i) => [i + 1, `Original ${i + 1}`]);
      await client.executeMany(
        `INSERT INTO ${TEST_TABLE} (id, data) VALUES (:1, :2)`,
        insertBinds
      );

      // Bulk update
      const updateBinds = Array.from({ length: 50 }, (_, i) => [`Updated ${i + 1}`, i + 1]);
      const result = await client.executeMany(
        `UPDATE ${TEST_TABLE} SET data = :1 WHERE id = :2`,
        updateBinds
      );

      expect(result.rowsAffected).toBe(50);
    });
  });

  describe('Error Handling', () => {
    it('should handle table not found error', async () => {
      await expect(
        client.execute('SELECT * FROM non_existent_table')
      ).rejects.toThrow();
    });

    it('should handle syntax error', async () => {
      await expect(
        client.execute('INVALID SQL SYNTAX')
      ).rejects.toThrow();
    });

    it('should handle constraint violation', async () => {
      const TEST_TABLE = 'test_constraint';

      await client.execute(`
        CREATE TABLE ${TEST_TABLE} (
          id NUMBER PRIMARY KEY,
          value VARCHAR2(100)
        )
      `);

      await client.execute(
        `INSERT INTO ${TEST_TABLE} (id, value) VALUES (1, 'first')`
      );

      await expect(
        client.execute(`INSERT INTO ${TEST_TABLE} (id, value) VALUES (1, 'duplicate')`)
      ).rejects.toThrow();

      await client.execute(`DROP TABLE ${TEST_TABLE}`);
    });

    it('should handle null constraint violation', async () => {
      const TEST_TABLE = 'test_null_constraint';

      await client.execute(`
        CREATE TABLE ${TEST_TABLE} (
          id NUMBER PRIMARY KEY,
          required_field VARCHAR2(100) NOT NULL
        )
      `);

      await expect(
        client.execute(`INSERT INTO ${TEST_TABLE} (id) VALUES (1)`)
      ).rejects.toThrow();

      await client.execute(`DROP TABLE ${TEST_TABLE}`);
    });
  });

  describe('Connection Pooling and Recovery', () => {
    it('should handle multiple sequential connections', async () => {
      for (let i = 0; i < 5; i++) {
        const testClient = new OracleTestClient(PDB_CONFIG);
        await testClient.connect();

        const result = await testClient.execute('SELECT 1 FROM DUAL');
        expect(result.rows).toHaveLength(1);

        await testClient.disconnect();
      }
    });

    it('should recover from error and continue', async () => {
      // Execute valid query
      const result1 = await client.execute('SELECT 1 FROM DUAL');
      expect(result1.rows).toHaveLength(1);

      // Execute invalid query
      try {
        await client.execute('INVALID QUERY');
      } catch (error) {
        // Expected error
      }

      // Should still work after error
      const result2 = await client.execute('SELECT 2 FROM DUAL');
      expect(result2.rows[0]['2']).toBe(2);
    });
  });

  describe('Performance Queries', () => {
    it('should execute EXPLAIN PLAN', async () => {
      await client.execute(`
        EXPLAIN PLAN FOR
        SELECT * FROM test_user.employees WHERE employee_id = 1001
      `);

      const result = await client.execute(`
        SELECT plan_table_output
        FROM TABLE(DBMS_XPLAN.DISPLAY())
      `);

      expect(result.rows.length).toBeGreaterThan(0);
    });

    it('should query execution statistics', async () => {
      const result = await client.execute(`
        SELECT
          sql_id,
          executions,
          elapsed_time,
          cpu_time,
          disk_reads,
          buffer_gets
        FROM v$sql
        WHERE ROWNUM <= 10
        ORDER BY elapsed_time DESC
      `);

      expect(result.rows.length).toBeGreaterThanOrEqual(0);
    });

    it('should measure query execution time', async () => {
      const startTime = Date.now();

      await client.execute(`
        SELECT * FROM test_user.employees WHERE is_active = 1
      `);

      const endTime = Date.now();
      const executionTime = endTime - startTime;

      expect(executionTime).toBeGreaterThan(0);
      expect(executionTime).toBeLessThan(5000); // Should complete in under 5 seconds
    });
  });

  describe('Test Data Verification', () => {
    it('should verify employees table data', async () => {
      const result = await client.execute(`
        SELECT COUNT(*) AS cnt FROM test_user.employees WHERE is_active = 1
      `);

      expect(result.rows[0].CNT).toBeGreaterThan(0);
    });

    it('should verify departments table data', async () => {
      const result = await client.execute(`
        SELECT COUNT(*) AS cnt FROM test_user.departments
      `);

      expect(result.rows[0].CNT).toBeGreaterThanOrEqual(4);
    });

    it('should verify projects table data', async () => {
      const result = await client.execute(`
        SELECT COUNT(*) AS cnt FROM test_user.projects
      `);

      expect(result.rows[0].CNT).toBeGreaterThan(0);
    });

    it('should verify employee_projects relationships', async () => {
      const result = await client.execute(`
        SELECT COUNT(*) AS cnt FROM test_user.employee_projects
      `);

      expect(result.rows[0].CNT).toBeGreaterThan(0);
    });
  });
});

describe('Oracle Cross-Container Tests', () => {
  it('should connect to both CDB and PDB', async () => {
    const cdbClient = new OracleTestClient(CDB_CONFIG);
    const pdbClient = new OracleTestClient(PDB_CONFIG);

    await cdbClient.connect();
    await pdbClient.connect();

    const cdbResult = await cdbClient.execute('SELECT USER FROM DUAL');
    const pdbResult = await pdbClient.execute('SELECT USER FROM DUAL');

    expect(cdbResult.rows[0].USER).toBe('SYS');
    expect(pdbResult.rows[0].USER).toBe('SYS');

    await cdbClient.disconnect();
    await pdbClient.disconnect();
  });
});
