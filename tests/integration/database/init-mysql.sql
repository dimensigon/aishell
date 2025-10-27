-- MySQL Test Database Initialization Script
-- Includes comprehensive test data and MySQL-specific features

-- Drop existing tables if they exist (in reverse order to handle foreign keys)
DROP TABLE IF EXISTS employee_audit;
DROP TABLE IF EXISTS project_assignments;
DROP TABLE IF EXISTS projects;
DROP TABLE IF EXISTS employees;
DROP TABLE IF EXISTS departments;
DROP TABLE IF EXISTS documents;
DROP TABLE IF EXISTS employee_view;

-- Create departments table
CREATE TABLE departments (
    dept_id INT AUTO_INCREMENT PRIMARY KEY,
    dept_name VARCHAR(100) NOT NULL UNIQUE,
    location VARCHAR(100),
    budget DECIMAL(12, 2) DEFAULT 0.00,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_dept_name (dept_name),
    INDEX idx_location (location)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create employees table
CREATE TABLE employees (
    emp_id INT AUTO_INCREMENT PRIMARY KEY,
    emp_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE,
    dept_id INT,
    salary DECIMAL(10, 2),
    hire_date DATE,
    status ENUM('active', 'inactive', 'on_leave') DEFAULT 'active',
    skills JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
        ON DELETE SET NULL
        ON UPDATE CASCADE,
    INDEX idx_emp_name (emp_name),
    INDEX idx_email (email),
    INDEX idx_dept_id (dept_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create projects table
CREATE TABLE projects (
    project_id INT AUTO_INCREMENT PRIMARY KEY,
    project_name VARCHAR(200) NOT NULL,
    description TEXT,
    dept_id INT,
    start_date DATE,
    end_date DATE,
    budget DECIMAL(12, 2),
    status ENUM('planning', 'active', 'completed', 'cancelled') DEFAULT 'planning',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    INDEX idx_project_name (project_name),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create project assignments (many-to-many)
CREATE TABLE project_assignments (
    assignment_id INT AUTO_INCREMENT PRIMARY KEY,
    emp_id INT NOT NULL,
    project_id INT NOT NULL,
    role VARCHAR(100),
    hours_allocated DECIMAL(5, 2),
    assigned_date DATE DEFAULT (CURRENT_DATE),
    FOREIGN KEY (emp_id) REFERENCES employees(emp_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    UNIQUE KEY unique_assignment (emp_id, project_id),
    INDEX idx_emp_id (emp_id),
    INDEX idx_project_id (project_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create audit table for trigger testing
CREATE TABLE employee_audit (
    audit_id INT AUTO_INCREMENT PRIMARY KEY,
    emp_id INT,
    action VARCHAR(50),
    old_salary DECIMAL(10, 2),
    new_salary DECIMAL(10, 2),
    changed_by VARCHAR(100),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create documents table for full-text search testing
CREATE TABLE documents (
    doc_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content TEXT,
    author VARCHAR(100),
    tags VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FULLTEXT KEY ft_title (title),
    FULLTEXT KEY ft_content (content),
    FULLTEXT KEY ft_title_content (title, content)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert test data for departments
INSERT INTO departments (dept_name, location, budget, metadata) VALUES
('Engineering', 'San Francisco', 1000000.00, JSON_OBJECT('floor', 3, 'employees', 50)),
('Marketing', 'New York', 500000.00, JSON_OBJECT('floor', 2, 'employees', 20)),
('Sales', 'Chicago', 750000.00, JSON_OBJECT('floor', 1, 'employees', 30)),
('HR', 'Boston', 300000.00, JSON_OBJECT('floor', 2, 'employees', 10)),
('Finance', 'San Francisco', 600000.00, JSON_OBJECT('floor', 4, 'employees', 15));

-- Insert test data for employees
INSERT INTO employees (emp_name, email, dept_id, salary, hire_date, status, skills) VALUES
('John Doe', 'john.doe@company.com', 1, 95000.00, '2020-01-15', 'active',
    JSON_ARRAY('Python', 'JavaScript', 'Docker')),
('Jane Smith', 'jane.smith@company.com', 1, 105000.00, '2019-03-20', 'active',
    JSON_ARRAY('Java', 'Kubernetes', 'AWS')),
('Bob Johnson', 'bob.johnson@company.com', 2, 75000.00, '2021-06-10', 'active',
    JSON_ARRAY('SEO', 'Content Marketing', 'Analytics')),
('Alice Williams', 'alice.williams@company.com', 3, 85000.00, '2020-09-01', 'active',
    JSON_ARRAY('Sales', 'CRM', 'Negotiation')),
('Charlie Brown', 'charlie.brown@company.com', 1, 88000.00, '2021-01-15', 'on_leave',
    JSON_ARRAY('Go', 'Microservices', 'gRPC')),
('Diana Prince', 'diana.prince@company.com', 4, 72000.00, '2022-02-20', 'active',
    JSON_ARRAY('Recruitment', 'Training', 'Employee Relations')),
('Eve Davis', 'eve.davis@company.com', 5, 98000.00, '2019-11-05', 'active',
    JSON_ARRAY('Accounting', 'Financial Analysis', 'Excel')),
('Frank Miller', 'frank.miller@company.com', 3, 82000.00, '2021-07-12', 'inactive',
    JSON_ARRAY('B2B Sales', 'Lead Generation'));

-- Insert test data for projects
INSERT INTO projects (project_name, description, dept_id, start_date, end_date, budget, status) VALUES
('Cloud Migration', 'Migrate infrastructure to AWS', 1, '2023-01-01', '2023-12-31', 500000.00, 'active'),
('Marketing Campaign Q1', 'Q1 2024 marketing initiatives', 2, '2024-01-01', '2024-03-31', 150000.00, 'completed'),
('Sales CRM Upgrade', 'Upgrade Salesforce CRM system', 3, '2023-06-01', '2024-06-30', 200000.00, 'active'),
('Employee Training Program', 'Annual training and development', 4, '2024-01-01', '2024-12-31', 100000.00, 'active'),
('Financial Audit 2024', 'Annual financial audit', 5, '2024-01-15', '2024-03-15', 50000.00, 'planning');

-- Insert test data for project assignments
INSERT INTO project_assignments (emp_id, project_id, role, hours_allocated, assigned_date) VALUES
(1, 1, 'Lead Developer', 160.00, '2023-01-01'),
(2, 1, 'DevOps Engineer', 160.00, '2023-01-01'),
(5, 1, 'Backend Developer', 120.00, '2023-02-01'),
(3, 2, 'Campaign Manager', 160.00, '2024-01-01'),
(4, 3, 'Sales Lead', 80.00, '2023-06-01'),
(6, 4, 'Training Coordinator', 160.00, '2024-01-01'),
(7, 5, 'Financial Analyst', 160.00, '2024-01-15');

-- Insert test data for documents (full-text search)
INSERT INTO documents (title, content, author, tags) VALUES
('MySQL Performance Tuning', 'Learn how to optimize MySQL queries for better performance. Indexes, query optimization, and caching strategies.', 'John Doe', 'mysql,performance,optimization'),
('Docker Best Practices', 'Best practices for containerizing applications with Docker. Multi-stage builds, layer optimization, security.', 'Jane Smith', 'docker,containers,devops'),
('JavaScript ES6 Features', 'Modern JavaScript features including arrow functions, promises, async/await, and destructuring.', 'John Doe', 'javascript,es6,programming'),
('AWS Lambda Tutorial', 'Complete guide to serverless computing with AWS Lambda. Event-driven architecture and scalability.', 'Jane Smith', 'aws,lambda,serverless'),
('Agile Methodology', 'Introduction to Agile software development practices. Scrum, Kanban, and continuous delivery.', 'Bob Johnson', 'agile,scrum,methodology');

-- Create trigger for salary changes audit
DELIMITER $$

CREATE TRIGGER audit_salary_changes
AFTER UPDATE ON employees
FOR EACH ROW
BEGIN
    IF NEW.salary != OLD.salary THEN
        INSERT INTO employee_audit (emp_id, action, old_salary, new_salary, changed_by)
        VALUES (NEW.emp_id, 'SALARY_UPDATE', OLD.salary, NEW.salary, USER());
    END IF;
END$$

DELIMITER ;

-- Create stored procedure to get employee details
DELIMITER $$

CREATE PROCEDURE GetEmployeeDetails(IN empId INT)
BEGIN
    SELECT
        e.emp_id,
        e.emp_name,
        e.email,
        e.salary,
        e.status,
        d.dept_name,
        d.location,
        COUNT(pa.project_id) as project_count
    FROM employees e
    LEFT JOIN departments d ON e.dept_id = d.dept_id
    LEFT JOIN project_assignments pa ON e.emp_id = pa.emp_id
    WHERE e.emp_id = empId
    GROUP BY e.emp_id, e.emp_name, e.email, e.salary, e.status, d.dept_name, d.location;
END$$

DELIMITER ;

-- Create stored function to calculate department total salary
DELIMITER $$

CREATE FUNCTION GetDepartmentSalaryTotal(deptId INT)
RETURNS DECIMAL(12, 2)
DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE total DECIMAL(12, 2);

    SELECT COALESCE(SUM(salary), 0) INTO total
    FROM employees
    WHERE dept_id = deptId AND status = 'active';

    RETURN total;
END$$

DELIMITER ;

-- Create view for employee summary
CREATE VIEW employee_view AS
SELECT
    e.emp_id,
    e.emp_name,
    e.email,
    e.salary,
    e.status,
    d.dept_name,
    d.location,
    COUNT(pa.project_id) as active_projects,
    GROUP_CONCAT(p.project_name SEPARATOR ', ') as project_names
FROM employees e
LEFT JOIN departments d ON e.dept_id = d.dept_id
LEFT JOIN project_assignments pa ON e.emp_id = pa.emp_id
LEFT JOIN projects p ON pa.project_id = p.project_id
WHERE e.status = 'active'
GROUP BY e.emp_id, e.emp_name, e.email, e.salary, e.status, d.dept_name, d.location;
