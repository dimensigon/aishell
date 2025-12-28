-- Oracle Database Test Data Initialization Script
-- For use with integration tests on CDB$ROOT and FREEPDB1

-- ============================================
-- SECTION 1: Test User and Schema Setup
-- ============================================

-- Create test user (run as SYS)
BEGIN
  EXECUTE IMMEDIATE 'DROP USER test_user CASCADE';
EXCEPTION
  WHEN OTHERS THEN NULL;
END;
/

CREATE USER test_user IDENTIFIED BY TestPass123
  DEFAULT TABLESPACE users
  TEMPORARY TABLESPACE temp
  QUOTA UNLIMITED ON users;

GRANT CONNECT, RESOURCE, CREATE VIEW, CREATE SEQUENCE TO test_user;

-- ============================================
-- SECTION 2: Sample Data Tables
-- ============================================

-- Employees table
CREATE TABLE test_user.employees (
  employee_id NUMBER(10) PRIMARY KEY,
  first_name VARCHAR2(50) NOT NULL,
  last_name VARCHAR2(50) NOT NULL,
  email VARCHAR2(100) UNIQUE NOT NULL,
  phone VARCHAR2(20),
  hire_date DATE DEFAULT SYSDATE,
  job_title VARCHAR2(100),
  salary NUMBER(10,2),
  department_id NUMBER(10),
  manager_id NUMBER(10),
  is_active NUMBER(1) DEFAULT 1,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Departments table
CREATE TABLE test_user.departments (
  department_id NUMBER(10) PRIMARY KEY,
  department_name VARCHAR2(100) NOT NULL,
  location VARCHAR2(100),
  budget NUMBER(12,2),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Projects table
CREATE TABLE test_user.projects (
  project_id NUMBER(10) PRIMARY KEY,
  project_name VARCHAR2(200) NOT NULL,
  description VARCHAR2(1000),
  start_date DATE,
  end_date DATE,
  status VARCHAR2(20) DEFAULT 'ACTIVE',
  budget NUMBER(12,2),
  department_id NUMBER(10),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Employee Projects junction table
CREATE TABLE test_user.employee_projects (
  employee_id NUMBER(10),
  project_id NUMBER(10),
  role VARCHAR2(100),
  hours_allocated NUMBER(5,2),
  PRIMARY KEY (employee_id, project_id),
  CONSTRAINT fk_emp_proj_emp FOREIGN KEY (employee_id)
    REFERENCES test_user.employees(employee_id) ON DELETE CASCADE,
  CONSTRAINT fk_emp_proj_proj FOREIGN KEY (project_id)
    REFERENCES test_user.projects(project_id) ON DELETE CASCADE
);

-- ============================================
-- SECTION 3: Sequences
-- ============================================

CREATE SEQUENCE test_user.emp_seq START WITH 1000 INCREMENT BY 1;
CREATE SEQUENCE test_user.dept_seq START WITH 100 INCREMENT BY 10;
CREATE SEQUENCE test_user.proj_seq START WITH 5000 INCREMENT BY 5;

-- ============================================
-- SECTION 4: Triggers
-- ============================================

-- Auto-update timestamp trigger
CREATE OR REPLACE TRIGGER test_user.trg_emp_updated_at
  BEFORE UPDATE ON test_user.employees
  FOR EACH ROW
BEGIN
  :NEW.updated_at := CURRENT_TIMESTAMP;
END;
/

-- Auto-assign employee_id from sequence
CREATE OR REPLACE TRIGGER test_user.trg_emp_id
  BEFORE INSERT ON test_user.employees
  FOR EACH ROW
  WHEN (NEW.employee_id IS NULL)
BEGIN
  SELECT test_user.emp_seq.NEXTVAL INTO :NEW.employee_id FROM DUAL;
END;
/

-- ============================================
-- SECTION 5: Stored Procedures
-- ============================================

-- Procedure to give employee raise
CREATE OR REPLACE PROCEDURE test_user.give_raise(
  p_employee_id IN NUMBER,
  p_percentage IN NUMBER,
  p_new_salary OUT NUMBER
)
AS
  v_current_salary NUMBER(10,2);
BEGIN
  SELECT salary INTO v_current_salary
  FROM test_user.employees
  WHERE employee_id = p_employee_id;

  p_new_salary := v_current_salary * (1 + p_percentage/100);

  UPDATE test_user.employees
  SET salary = p_new_salary
  WHERE employee_id = p_employee_id;

  COMMIT;
EXCEPTION
  WHEN NO_DATA_FOUND THEN
    RAISE_APPLICATION_ERROR(-20001, 'Employee not found');
END;
/

-- Procedure to assign employee to project
CREATE OR REPLACE PROCEDURE test_user.assign_to_project(
  p_employee_id IN NUMBER,
  p_project_id IN NUMBER,
  p_role IN VARCHAR2,
  p_hours IN NUMBER DEFAULT 40
)
AS
BEGIN
  INSERT INTO test_user.employee_projects
    (employee_id, project_id, role, hours_allocated)
  VALUES
    (p_employee_id, p_project_id, p_role, p_hours);

  COMMIT;
EXCEPTION
  WHEN DUP_VAL_ON_INDEX THEN
    UPDATE test_user.employee_projects
    SET role = p_role, hours_allocated = p_hours
    WHERE employee_id = p_employee_id AND project_id = p_project_id;
    COMMIT;
END;
/

-- ============================================
-- SECTION 6: Functions
-- ============================================

-- Function to calculate total salary by department
CREATE OR REPLACE FUNCTION test_user.get_dept_salary_total(
  p_department_id IN NUMBER
)
RETURN NUMBER
IS
  v_total NUMBER(12,2);
BEGIN
  SELECT NVL(SUM(salary), 0) INTO v_total
  FROM test_user.employees
  WHERE department_id = p_department_id
    AND is_active = 1;

  RETURN v_total;
END;
/

-- Function to get employee full name
CREATE OR REPLACE FUNCTION test_user.get_full_name(
  p_employee_id IN NUMBER
)
RETURN VARCHAR2
IS
  v_name VARCHAR2(200);
BEGIN
  SELECT first_name || ' ' || last_name INTO v_name
  FROM test_user.employees
  WHERE employee_id = p_employee_id;

  RETURN v_name;
EXCEPTION
  WHEN NO_DATA_FOUND THEN
    RETURN NULL;
END;
/

-- ============================================
-- SECTION 7: Views
-- ============================================

-- View: Employee details with department info
CREATE OR REPLACE VIEW test_user.v_employee_details AS
SELECT
  e.employee_id,
  e.first_name || ' ' || e.last_name AS full_name,
  e.email,
  e.job_title,
  e.salary,
  d.department_name,
  d.location,
  e.hire_date,
  FLOOR(MONTHS_BETWEEN(SYSDATE, e.hire_date) / 12) AS years_of_service
FROM test_user.employees e
LEFT JOIN test_user.departments d ON e.department_id = d.department_id
WHERE e.is_active = 1;

-- View: Project summary
CREATE OR REPLACE VIEW test_user.v_project_summary AS
SELECT
  p.project_id,
  p.project_name,
  p.status,
  d.department_name,
  COUNT(ep.employee_id) AS team_size,
  SUM(ep.hours_allocated) AS total_hours
FROM test_user.projects p
LEFT JOIN test_user.departments d ON p.department_id = d.department_id
LEFT JOIN test_user.employee_projects ep ON p.project_id = ep.project_id
GROUP BY p.project_id, p.project_name, p.status, d.department_name;

-- ============================================
-- SECTION 8: Sample Test Data
-- ============================================

-- Insert departments
INSERT INTO test_user.departments (department_id, department_name, location, budget)
VALUES (100, 'Engineering', 'San Francisco', 5000000);

INSERT INTO test_user.departments (department_id, department_name, location, budget)
VALUES (110, 'Sales', 'New York', 3000000);

INSERT INTO test_user.departments (department_id, department_name, location, budget)
VALUES (120, 'Marketing', 'Los Angeles', 2000000);

INSERT INTO test_user.departments (department_id, department_name, location, budget)
VALUES (130, 'HR', 'Chicago', 1500000);

-- Insert employees
INSERT INTO test_user.employees
  (employee_id, first_name, last_name, email, phone, hire_date, job_title, salary, department_id, manager_id)
VALUES
  (1001, 'John', 'Smith', 'john.smith@example.com', '555-0101', DATE '2020-01-15', 'Senior Engineer', 120000, 100, NULL);

INSERT INTO test_user.employees
  (employee_id, first_name, last_name, email, phone, hire_date, job_title, salary, department_id, manager_id)
VALUES
  (1002, 'Sarah', 'Johnson', 'sarah.j@example.com', '555-0102', DATE '2020-03-20', 'Software Engineer', 95000, 100, 1001);

INSERT INTO test_user.employees
  (employee_id, first_name, last_name, email, phone, hire_date, job_title, salary, department_id, manager_id)
VALUES
  (1003, 'Michael', 'Williams', 'michael.w@example.com', '555-0103', DATE '2019-06-10', 'Sales Manager', 110000, 110, NULL);

INSERT INTO test_user.employees
  (employee_id, first_name, last_name, email, phone, hire_date, job_title, salary, department_id, manager_id)
VALUES
  (1004, 'Emily', 'Davis', 'emily.d@example.com', '555-0104', DATE '2021-02-01', 'Marketing Specialist', 75000, 120, NULL);

INSERT INTO test_user.employees
  (employee_id, first_name, last_name, email, phone, hire_date, job_title, salary, department_id, manager_id)
VALUES
  (1005, 'David', 'Brown', 'david.b@example.com', '555-0105', DATE '2021-08-15', 'Junior Developer', 70000, 100, 1002);

INSERT INTO test_user.employees
  (employee_id, first_name, last_name, email, phone, hire_date, job_title, salary, department_id, manager_id)
VALUES
  (1006, 'Lisa', 'Anderson', 'lisa.a@example.com', '555-0106', DATE '2018-11-30', 'HR Manager', 95000, 130, NULL);

-- Insert projects
INSERT INTO test_user.projects
  (project_id, project_name, description, start_date, end_date, status, budget, department_id)
VALUES
  (5001, 'Cloud Migration', 'Migrate legacy systems to cloud', DATE '2024-01-01', DATE '2024-12-31', 'ACTIVE', 2000000, 100);

INSERT INTO test_user.projects
  (project_id, project_name, description, start_date, end_date, status, budget, department_id)
VALUES
  (5002, 'Mobile App Development', 'Build customer mobile application', DATE '2024-03-01', DATE '2024-09-30', 'ACTIVE', 1500000, 100);

INSERT INTO test_user.projects
  (project_id, project_name, description, start_date, end_date, status, budget, department_id)
VALUES
  (5003, 'Q4 Sales Campaign', 'End of year sales push', DATE '2024-10-01', DATE '2024-12-31', 'PLANNING', 500000, 110);

-- Assign employees to projects
INSERT INTO test_user.employee_projects (employee_id, project_id, role, hours_allocated)
VALUES (1001, 5001, 'Tech Lead', 40);

INSERT INTO test_user.employee_projects (employee_id, project_id, role, hours_allocated)
VALUES (1002, 5001, 'Senior Developer', 40);

INSERT INTO test_user.employee_projects (employee_id, project_id, role, hours_allocated)
VALUES (1005, 5001, 'Junior Developer', 35);

INSERT INTO test_user.employee_projects (employee_id, project_id, role, hours_allocated)
VALUES (1002, 5002, 'Lead Developer', 30);

INSERT INTO test_user.employee_projects (employee_id, project_id, role, hours_allocated)
VALUES (1005, 5002, 'Developer', 20);

INSERT INTO test_user.employee_projects (employee_id, project_id, role, hours_allocated)
VALUES (1003, 5003, 'Campaign Manager', 40);

COMMIT;

-- ============================================
-- SECTION 9: Indexes for Performance Testing
-- ============================================

CREATE INDEX idx_emp_dept ON test_user.employees(department_id);
CREATE INDEX idx_emp_manager ON test_user.employees(manager_id);
CREATE INDEX idx_emp_email ON test_user.employees(email);
CREATE INDEX idx_proj_dept ON test_user.projects(department_id);
CREATE INDEX idx_proj_status ON test_user.projects(status);

-- ============================================
-- SECTION 10: Package for Complex Operations
-- ============================================

CREATE OR REPLACE PACKAGE test_user.employee_pkg AS
  -- Package specification
  PROCEDURE hire_employee(
    p_first_name VARCHAR2,
    p_last_name VARCHAR2,
    p_email VARCHAR2,
    p_job_title VARCHAR2,
    p_salary NUMBER,
    p_department_id NUMBER,
    p_employee_id OUT NUMBER
  );

  FUNCTION get_active_count RETURN NUMBER;

  PROCEDURE terminate_employee(
    p_employee_id NUMBER
  );
END employee_pkg;
/

CREATE OR REPLACE PACKAGE BODY test_user.employee_pkg AS

  PROCEDURE hire_employee(
    p_first_name VARCHAR2,
    p_last_name VARCHAR2,
    p_email VARCHAR2,
    p_job_title VARCHAR2,
    p_salary NUMBER,
    p_department_id NUMBER,
    p_employee_id OUT NUMBER
  ) AS
  BEGIN
    INSERT INTO test_user.employees
      (first_name, last_name, email, job_title, salary, department_id, hire_date)
    VALUES
      (p_first_name, p_last_name, p_email, p_job_title, p_salary, p_department_id, SYSDATE)
    RETURNING employee_id INTO p_employee_id;

    COMMIT;
  END hire_employee;

  FUNCTION get_active_count RETURN NUMBER AS
    v_count NUMBER;
  BEGIN
    SELECT COUNT(*) INTO v_count
    FROM test_user.employees
    WHERE is_active = 1;

    RETURN v_count;
  END get_active_count;

  PROCEDURE terminate_employee(
    p_employee_id NUMBER
  ) AS
  BEGIN
    UPDATE test_user.employees
    SET is_active = 0
    WHERE employee_id = p_employee_id;

    COMMIT;
  END terminate_employee;

END employee_pkg;
/

-- Grant permissions
GRANT EXECUTE ON test_user.give_raise TO PUBLIC;
GRANT EXECUTE ON test_user.assign_to_project TO PUBLIC;
GRANT EXECUTE ON test_user.get_dept_salary_total TO PUBLIC;
GRANT EXECUTE ON test_user.get_full_name TO PUBLIC;
GRANT EXECUTE ON test_user.employee_pkg TO PUBLIC;

-- Display summary
SELECT 'Oracle test data initialized successfully' AS status FROM DUAL;
SELECT COUNT(*) AS employee_count FROM test_user.employees;
SELECT COUNT(*) AS department_count FROM test_user.departments;
SELECT COUNT(*) AS project_count FROM test_user.projects;
