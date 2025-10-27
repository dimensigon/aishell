-- MySQL Initialization Script
-- Sets up test database, tables, sample data, indexes, and constraints

-- Create and use test database
CREATE DATABASE IF NOT EXISTS testdb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE testdb;

-- Drop existing tables if they exist
DROP TABLE IF EXISTS project_assignments;
DROP TABLE IF EXISTS projects;
DROP TABLE IF EXISTS employees;
DROP TABLE IF EXISTS departments;
DROP TABLE IF EXISTS employee_audit;

-- ====================================
-- DEPARTMENTS Table
-- ====================================
CREATE TABLE departments (
    department_id INT AUTO_INCREMENT PRIMARY KEY,
    department_name VARCHAR(100) NOT NULL UNIQUE,
    department_code VARCHAR(10) NOT NULL UNIQUE,
    manager_id INT,
    budget DECIMAL(12, 2) DEFAULT 0.00,
    location VARCHAR(100),
    phone VARCHAR(20),
    email VARCHAR(100),
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_department_code (department_code),
    INDEX idx_active (active)
) ENGINE=InnoDB;

-- Insert sample departments
INSERT INTO departments (department_name, department_code, budget, location, phone, email, active) VALUES
('Engineering', 'ENG', 2500000.00, 'Building A - Floor 3', '+1-555-0301', 'engineering@company.com', TRUE),
('Product Management', 'PROD', 1200000.00, 'Building A - Floor 2', '+1-555-0302', 'product@company.com', TRUE),
('Design', 'DES', 800000.00, 'Building B - Floor 1', '+1-555-0303', 'design@company.com', TRUE),
('Sales', 'SALES', 1800000.00, 'Building C - Floor 1', '+1-555-0304', 'sales@company.com', TRUE),
('Marketing', 'MKT', 1500000.00, 'Building C - Floor 2', '+1-555-0305', 'marketing@company.com', TRUE),
('Human Resources', 'HR', 600000.00, 'Building A - Floor 1', '+1-555-0306', 'hr@company.com', TRUE),
('Finance', 'FIN', 900000.00, 'Building A - Floor 4', '+1-555-0307', 'finance@company.com', TRUE),
('Customer Support', 'SUP', 700000.00, 'Building D - Floor 1', '+1-555-0308', 'support@company.com', TRUE),
('IT Operations', 'IT', 1100000.00, 'Building A - Floor 5', '+1-555-0309', 'it@company.com', TRUE),
('Legal', 'LEG', 500000.00, 'Building A - Floor 1', '+1-555-0310', 'legal@company.com', TRUE);

-- ====================================
-- EMPLOYEES Table
-- ====================================
CREATE TABLE employees (
    employee_id INT AUTO_INCREMENT PRIMARY KEY,
    employee_number VARCHAR(20) NOT NULL UNIQUE,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone VARCHAR(20),
    department_id INT,
    job_title VARCHAR(100) NOT NULL,
    hire_date DATE NOT NULL,
    salary DECIMAL(10, 2) NOT NULL,
    commission_pct DECIMAL(3, 2),
    manager_id INT,
    employment_status ENUM('active', 'on_leave', 'terminated') DEFAULT 'active',
    address_line1 VARCHAR(200),
    address_line2 VARCHAR(200),
    city VARCHAR(100),
    state VARCHAR(50),
    postal_code VARCHAR(20),
    country VARCHAR(50) DEFAULT 'USA',
    birth_date DATE,
    ssn_last4 VARCHAR(4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (department_id) REFERENCES departments(department_id) ON DELETE SET NULL,
    FOREIGN KEY (manager_id) REFERENCES employees(employee_id) ON DELETE SET NULL,
    INDEX idx_department_id (department_id),
    INDEX idx_manager_id (manager_id),
    INDEX idx_email (email),
    INDEX idx_hire_date (hire_date),
    INDEX idx_status (employment_status),
    INDEX idx_name (last_name, first_name)
) ENGINE=InnoDB;

-- Insert sample employees
INSERT INTO employees (employee_number, first_name, last_name, email, phone, department_id, job_title, hire_date, salary, commission_pct, manager_id, employment_status, city, state, postal_code, birth_date, ssn_last4) VALUES
-- Engineering Department
('EMP-001', 'Sarah', 'Johnson', 'sarah.johnson@company.com', '+1-555-1001', 1, 'VP of Engineering', '2020-01-15', 185000.00, NULL, NULL, 'active', 'San Francisco', 'CA', '94102', '1985-03-20', '7890'),
('EMP-002', 'Michael', 'Chen', 'michael.chen@company.com', '+1-555-1002', 1, 'Senior Software Engineer', '2021-03-10', 145000.00, NULL, 1, 'active', 'San Francisco', 'CA', '94103', '1988-07-15', '1234'),
('EMP-003', 'Emily', 'Rodriguez', 'emily.rodriguez@company.com', '+1-555-1003', 1, 'Software Engineer', '2022-06-01', 120000.00, NULL, 1, 'active', 'Oakland', 'CA', '94612', '1992-11-08', '5678'),
('EMP-004', 'David', 'Kim', 'david.kim@company.com', '+1-555-1004', 1, 'DevOps Engineer', '2021-09-15', 135000.00, NULL, 1, 'active', 'Berkeley', 'CA', '94704', '1990-05-22', '9012'),

-- Product Management
('EMP-005', 'Jessica', 'Martinez', 'jessica.martinez@company.com', '+1-555-2001', 2, 'Chief Product Officer', '2019-08-01', 195000.00, NULL, NULL, 'active', 'Palo Alto', 'CA', '94301', '1983-09-12', '3456'),
('EMP-006', 'Robert', 'Taylor', 'robert.taylor@company.com', '+1-555-2002', 2, 'Senior Product Manager', '2021-02-20', 155000.00, NULL, 5, 'active', 'Mountain View', 'CA', '94040', '1987-12-05', '7891'),
('EMP-007', 'Amanda', 'White', 'amanda.white@company.com', '+1-555-2003', 2, 'Product Manager', '2022-11-10', 130000.00, NULL, 5, 'active', 'San Jose', 'CA', '95110', '1991-04-18', '2345'),

-- Design
('EMP-008', 'Christopher', 'Brown', 'christopher.brown@company.com', '+1-555-3001', 3, 'Design Director', '2020-05-12', 160000.00, NULL, NULL, 'active', 'San Francisco', 'CA', '94110', '1986-08-30', '6789'),
('EMP-009', 'Michelle', 'Davis', 'michelle.davis@company.com', '+1-555-3002', 3, 'Senior UX Designer', '2021-07-25', 125000.00, NULL, 8, 'active', 'San Francisco', 'CA', '94115', '1989-02-14', '0123'),
('EMP-010', 'Daniel', 'Wilson', 'daniel.wilson@company.com', '+1-555-3003', 3, 'UI Designer', '2023-01-08', 105000.00, NULL, 8, 'active', 'Daly City', 'CA', '94014', '1993-10-27', '4567'),

-- Sales
('EMP-011', 'Jennifer', 'Anderson', 'jennifer.anderson@company.com', '+1-555-4001', 4, 'VP of Sales', '2019-03-15', 175000.00, 0.15, NULL, 'active', 'New York', 'NY', '10001', '1984-06-07', '8901'),
('EMP-012', 'James', 'Thomas', 'james.thomas@company.com', '+1-555-4002', 4, 'Senior Account Executive', '2020-10-20', 125000.00, 0.12, 11, 'active', 'New York', 'NY', '10013', '1988-01-25', '2346'),
('EMP-013', 'Lisa', 'Garcia', 'lisa.garcia@company.com', '+1-555-4003', 4, 'Account Executive', '2022-04-15', 95000.00, 0.10, 11, 'active', 'Brooklyn', 'NY', '11201', '1991-09-30', '5679'),

-- Marketing
('EMP-014', 'Kevin', 'Lee', 'kevin.lee@company.com', '+1-555-5001', 5, 'CMO', '2018-11-01', 190000.00, NULL, NULL, 'active', 'Austin', 'TX', '78701', '1982-04-16', '9013'),
('EMP-015', 'Rachel', 'Moore', 'rachel.moore@company.com', '+1-555-5002', 5, 'Marketing Manager', '2021-05-18', 115000.00, NULL, 14, 'active', 'Austin', 'TX', '78702', '1990-11-22', '3457'),

-- HR
('EMP-016', 'Thomas', 'Jackson', 'thomas.jackson@company.com', '+1-555-6001', 6, 'HR Director', '2020-02-10', 140000.00, NULL, NULL, 'active', 'Seattle', 'WA', '98101', '1985-07-08', '7892'),
('EMP-017', 'Nicole', 'Harris', 'nicole.harris@company.com', '+1-555-6002', 6, 'HR Specialist', '2022-08-22', 85000.00, NULL, 16, 'active', 'Seattle', 'WA', '98103', '1992-03-14', '1235'),

-- Finance
('EMP-018', 'William', 'Martin', 'william.martin@company.com', '+1-555-7001', 7, 'CFO', '2019-06-15', 200000.00, NULL, NULL, 'active', 'Chicago', 'IL', '60601', '1980-12-01', '5680'),
('EMP-019', 'Sophia', 'Thompson', 'sophia.thompson@company.com', '+1-555-7002', 7, 'Senior Accountant', '2021-09-30', 95000.00, NULL, 18, 'active', 'Chicago', 'IL', '60602', '1989-05-19', '9014'),

-- Customer Support
('EMP-020', 'Brian', 'Clark', 'brian.clark@company.com', '+1-555-8001', 8, 'Support Manager', '2020-12-01', 110000.00, NULL, NULL, 'active', 'Denver', 'CO', '80202', '1987-10-11', '3458');

-- Update department managers
UPDATE departments SET manager_id = 1 WHERE department_code = 'ENG';
UPDATE departments SET manager_id = 5 WHERE department_code = 'PROD';
UPDATE departments SET manager_id = 8 WHERE department_code = 'DES';
UPDATE departments SET manager_id = 11 WHERE department_code = 'SALES';
UPDATE departments SET manager_id = 14 WHERE department_code = 'MKT';
UPDATE departments SET manager_id = 16 WHERE department_code = 'HR';
UPDATE departments SET manager_id = 18 WHERE department_code = 'FIN';
UPDATE departments SET manager_id = 20 WHERE department_code = 'SUP';

-- ====================================
-- PROJECTS Table
-- ====================================
CREATE TABLE projects (
    project_id INT AUTO_INCREMENT PRIMARY KEY,
    project_code VARCHAR(20) NOT NULL UNIQUE,
    project_name VARCHAR(200) NOT NULL,
    description TEXT,
    department_id INT,
    project_manager_id INT,
    budget DECIMAL(12, 2),
    actual_cost DECIMAL(12, 2) DEFAULT 0.00,
    start_date DATE,
    end_date DATE,
    deadline DATE,
    status ENUM('planning', 'in_progress', 'on_hold', 'completed', 'cancelled') DEFAULT 'planning',
    priority ENUM('low', 'medium', 'high', 'critical') DEFAULT 'medium',
    completion_percentage INT DEFAULT 0 CHECK (completion_percentage BETWEEN 0 AND 100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (department_id) REFERENCES departments(department_id) ON DELETE SET NULL,
    FOREIGN KEY (project_manager_id) REFERENCES employees(employee_id) ON DELETE SET NULL,
    INDEX idx_status (status),
    INDEX idx_department_id (department_id),
    INDEX idx_dates (start_date, end_date),
    INDEX idx_priority (priority)
) ENGINE=InnoDB;

-- Insert sample projects
INSERT INTO projects (project_code, project_name, description, department_id, project_manager_id, budget, actual_cost, start_date, end_date, deadline, status, priority, completion_percentage) VALUES
('PROJ-2025-001', 'Mobile App Redesign', 'Complete redesign of mobile application with new features', 1, 2, 450000.00, 387000.00, '2025-01-15', NULL, '2025-12-31', 'in_progress', 'high', 65),
('PROJ-2025-002', 'API Platform v2', 'Build next generation API platform with microservices', 1, 2, 600000.00, 245000.00, '2025-03-01', NULL, '2025-11-30', 'in_progress', 'critical', 42),
('PROJ-2025-003', 'Customer Portal', 'Self-service customer portal for account management', 1, 4, 320000.00, 95000.00, '2025-05-10', NULL, '2026-02-28', 'in_progress', 'medium', 28),
('PROJ-2024-015', 'Payment Gateway Integration', 'Integrate multiple payment providers', 1, 2, 180000.00, 182000.00, '2024-08-01', '2025-10-15', '2025-10-31', 'completed', 'high', 100),
('PROJ-2025-004', 'Marketing Automation', 'Implement automated marketing campaigns', 5, 15, 275000.00, 125000.00, '2025-04-01', NULL, '2025-12-15', 'in_progress', 'medium', 45),
('PROJ-2025-005', 'Sales CRM Upgrade', 'Upgrade and customize Salesforce CRM', 4, 12, 195000.00, 0.00, '2025-11-01', NULL, '2026-04-30', 'planning', 'medium', 0),
('PROJ-2024-022', 'Brand Refresh', 'Company-wide brand identity refresh', 3, 8, 420000.00, 425000.00, '2024-06-01', '2025-09-30', '2025-10-15', 'completed', 'high', 100),
('PROJ-2025-006', 'Data Analytics Platform', 'Build internal analytics and reporting platform', 1, 4, 550000.00, 215000.00, '2025-02-15', NULL, '2026-01-31', 'in_progress', 'high', 38),
('PROJ-2025-007', 'Employee Onboarding System', 'Automated employee onboarding workflow', 6, 16, 145000.00, 72000.00, '2025-06-01', NULL, '2025-12-31', 'in_progress', 'low', 51),
('PROJ-2025-008', 'Infrastructure Migration', 'Migrate infrastructure to cloud platform', 9, 4, 780000.00, 325000.00, '2025-01-20', NULL, '2025-11-15', 'in_progress', 'critical', 55);

-- ====================================
-- PROJECT_ASSIGNMENTS Table
-- ====================================
CREATE TABLE project_assignments (
    assignment_id INT AUTO_INCREMENT PRIMARY KEY,
    project_id INT NOT NULL,
    employee_id INT NOT NULL,
    role VARCHAR(100),
    allocation_percentage INT DEFAULT 100 CHECK (allocation_percentage BETWEEN 1 AND 100),
    start_date DATE NOT NULL,
    end_date DATE,
    billable_rate DECIMAL(8, 2),
    hours_worked DECIMAL(8, 2) DEFAULT 0.00,
    active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE CASCADE,
    UNIQUE KEY unique_assignment (project_id, employee_id, start_date),
    INDEX idx_project_id (project_id),
    INDEX idx_employee_id (employee_id),
    INDEX idx_active (active)
) ENGINE=InnoDB;

-- Insert sample project assignments
INSERT INTO project_assignments (project_id, employee_id, role, allocation_percentage, start_date, end_date, billable_rate, hours_worked, active) VALUES
-- Mobile App Redesign
(1, 2, 'Tech Lead', 50, '2025-01-15', NULL, 175.00, 520.50, TRUE),
(1, 3, 'Developer', 100, '2025-01-15', NULL, 140.00, 650.00, TRUE),
(1, 9, 'UX Designer', 75, '2025-01-20', NULL, 150.00, 485.25, TRUE),
(1, 10, 'UI Designer', 100, '2025-01-20', NULL, 125.00, 598.00, TRUE),

-- API Platform v2
(2, 2, 'Project Manager', 50, '2025-03-01', NULL, 175.00, 245.00, TRUE),
(2, 3, 'Senior Developer', 75, '2025-03-01', NULL, 140.00, 312.50, TRUE),
(2, 4, 'DevOps Engineer', 100, '2025-03-05', NULL, 160.00, 385.00, TRUE),

-- Customer Portal
(3, 4, 'Tech Lead', 75, '2025-05-10', NULL, 160.00, 158.25, TRUE),
(3, 10, 'Designer', 50, '2025-05-15', NULL, 125.00, 95.50, TRUE),

-- Payment Gateway (Completed)
(4, 2, 'Tech Lead', 100, '2024-08-01', '2025-10-15', 175.00, 1250.00, FALSE),
(4, 3, 'Developer', 100, '2024-08-01', '2025-10-15', 140.00, 1180.00, FALSE),

-- Marketing Automation
(5, 15, 'Project Manager', 80, '2025-04-01', NULL, 135.00, 285.00, TRUE),

-- Data Analytics Platform
(8, 4, 'Tech Lead', 50, '2025-02-15', NULL, 160.00, 425.75, TRUE),
(8, 2, 'Consultant', 25, '2025-02-15', NULL, 175.00, 128.50, TRUE),

-- Employee Onboarding System
(9, 16, 'Project Manager', 40, '2025-06-01', NULL, 155.00, 168.00, TRUE),
(9, 17, 'Business Analyst', 60, '2025-06-01', NULL, 95.00, 195.50, TRUE),

-- Infrastructure Migration
(10, 4, 'Project Manager', 60, '2025-01-20', NULL, 160.00, 512.00, TRUE);

-- ====================================
-- EMPLOYEE_AUDIT Table (for triggers)
-- ====================================
CREATE TABLE employee_audit (
    audit_id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT,
    action VARCHAR(20),
    old_salary DECIMAL(10, 2),
    new_salary DECIMAL(10, 2),
    old_status VARCHAR(20),
    new_status VARCHAR(20),
    changed_by VARCHAR(100),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ====================================
-- CREATE VIEWS
-- ====================================

-- Department summary view
CREATE OR REPLACE VIEW department_summary AS
SELECT
    d.department_id,
    d.department_name,
    d.department_code,
    CONCAT(m.first_name, ' ', m.last_name) AS manager_name,
    COUNT(DISTINCT e.employee_id) AS employee_count,
    COUNT(DISTINCT p.project_id) AS active_projects,
    d.budget AS department_budget,
    COALESCE(SUM(p.budget), 0) AS total_project_budget,
    d.location
FROM departments d
LEFT JOIN employees m ON d.manager_id = m.employee_id
LEFT JOIN employees e ON d.department_id = e.department_id AND e.employment_status = 'active'
LEFT JOIN projects p ON d.department_id = p.department_id AND p.status IN ('planning', 'in_progress')
GROUP BY d.department_id, d.department_name, d.department_code, manager_name, d.budget, d.location;

-- Project status view
CREATE OR REPLACE VIEW project_status_view AS
SELECT
    p.project_id,
    p.project_code,
    p.project_name,
    d.department_name,
    CONCAT(pm.first_name, ' ', pm.last_name) AS project_manager,
    p.status,
    p.priority,
    p.budget,
    p.actual_cost,
    p.budget - p.actual_cost AS remaining_budget,
    p.completion_percentage,
    p.start_date,
    p.deadline,
    DATEDIFF(p.deadline, CURDATE()) AS days_until_deadline,
    COUNT(DISTINCT pa.employee_id) AS team_size,
    COALESCE(SUM(pa.hours_worked), 0) AS total_hours
FROM projects p
LEFT JOIN departments d ON p.department_id = d.department_id
LEFT JOIN employees pm ON p.project_manager_id = pm.employee_id
LEFT JOIN project_assignments pa ON p.project_id = pa.project_id AND pa.active = TRUE
GROUP BY p.project_id, p.project_code, p.project_name, d.department_name, project_manager,
         p.status, p.priority, p.budget, p.actual_cost, p.completion_percentage,
         p.start_date, p.deadline;

-- Employee workload view
CREATE OR REPLACE VIEW employee_workload AS
SELECT
    e.employee_id,
    e.employee_number,
    CONCAT(e.first_name, ' ', e.last_name) AS employee_name,
    e.job_title,
    d.department_name,
    COUNT(DISTINCT pa.project_id) AS active_projects,
    SUM(pa.allocation_percentage) AS total_allocation,
    COALESCE(SUM(pa.hours_worked), 0) AS total_hours_worked
FROM employees e
LEFT JOIN departments d ON e.department_id = d.department_id
LEFT JOIN project_assignments pa ON e.employee_id = pa.employee_id AND pa.active = TRUE
WHERE e.employment_status = 'active'
GROUP BY e.employee_id, e.employee_number, employee_name, e.job_title, d.department_name;

-- ====================================
-- CREATE TRIGGERS
-- ====================================

DELIMITER //

-- Trigger to audit salary changes
CREATE TRIGGER before_employee_salary_update
BEFORE UPDATE ON employees
FOR EACH ROW
BEGIN
    IF OLD.salary != NEW.salary OR OLD.employment_status != NEW.employment_status THEN
        INSERT INTO employee_audit (employee_id, action, old_salary, new_salary, old_status, new_status, changed_by)
        VALUES (OLD.employee_id, 'UPDATE', OLD.salary, NEW.salary, OLD.employment_status, NEW.employment_status, USER());
    END IF;
END//

DELIMITER ;

-- ====================================
-- CREATE STORED PROCEDURES
-- ====================================

DELIMITER //

-- Procedure to get department statistics
CREATE PROCEDURE GetDepartmentStats(IN dept_id INT)
BEGIN
    SELECT
        d.department_name,
        COUNT(DISTINCT e.employee_id) AS total_employees,
        AVG(e.salary) AS average_salary,
        SUM(e.salary) AS total_payroll,
        COUNT(DISTINCT p.project_id) AS active_projects,
        SUM(p.budget) AS total_project_budget
    FROM departments d
    LEFT JOIN employees e ON d.department_id = e.department_id AND e.employment_status = 'active'
    LEFT JOIN projects p ON d.department_id = p.department_id AND p.status IN ('planning', 'in_progress')
    WHERE d.department_id = dept_id
    GROUP BY d.department_name;
END//

DELIMITER ;

-- ====================================
-- Summary
-- ====================================
SELECT 'MySQL initialization complete!' AS status;
SELECT CONCAT(COUNT(*), ' departments created') AS departments FROM departments;
SELECT CONCAT(COUNT(*), ' employees created') AS employees FROM employees;
SELECT CONCAT(COUNT(*), ' projects created') AS projects FROM projects;
SELECT CONCAT(COUNT(*), ' project assignments created') AS assignments FROM project_assignments;
