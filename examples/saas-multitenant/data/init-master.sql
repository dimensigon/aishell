-- SaaS Multi-Tenant Master Database Schema
-- This schema manages tenant metadata and routing

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Tenant plans
CREATE TABLE plans (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    display_name VARCHAR(100) NOT NULL,
    max_users INTEGER NOT NULL,
    max_storage_gb INTEGER NOT NULL,
    max_api_calls_per_day INTEGER NOT NULL,
    price_monthly DECIMAL(10, 2) NOT NULL,
    features JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default plans
INSERT INTO plans (name, display_name, max_users, max_storage_gb, max_api_calls_per_day, price_monthly, features) VALUES
('free', 'Free', 5, 1, 1000, 0.00, '{"support": "community", "sla": false}'),
('starter', 'Starter', 10, 10, 10000, 29.00, '{"support": "email", "sla": false, "custom_domain": false}'),
('professional', 'Professional', 50, 50, 100000, 99.00, '{"support": "email", "sla": "99%", "custom_domain": true, "api_access": true}'),
('enterprise', 'Enterprise', 999999, 500, 1000000, 499.00, '{"support": "24/7", "sla": "99.9%", "custom_domain": true, "api_access": true, "dedicated_instance": true}');

-- Tenants table (master registry)
CREATE TABLE tenants (
    id SERIAL PRIMARY KEY,
    tenant_key VARCHAR(50) NOT NULL UNIQUE, -- Used for schema naming
    company_name VARCHAR(255) NOT NULL,
    subdomain VARCHAR(100) UNIQUE,
    custom_domain VARCHAR(255),
    plan_id INTEGER REFERENCES plans(id),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'cancelled', 'trial')),
    schema_name VARCHAR(63) NOT NULL UNIQUE, -- PostgreSQL schema name
    database_instance VARCHAR(100) DEFAULT 'primary', -- For sharding
    max_users INTEGER,
    max_storage_gb INTEGER,
    current_users INTEGER DEFAULT 0,
    current_storage_gb DECIMAL(10, 2) DEFAULT 0,
    settings JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    trial_ends_at TIMESTAMP,
    subscription_ends_at TIMESTAMP
);

-- Tenant admins
CREATE TABLE tenant_admins (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER REFERENCES tenants(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    password_hash VARCHAR(255) NOT NULL,
    is_primary BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    UNIQUE(tenant_id, email)
);

-- Usage tracking (for billing)
CREATE TABLE tenant_usage (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER REFERENCES tenants(id) ON DELETE CASCADE,
    metric_type VARCHAR(50) NOT NULL, -- users, storage, api_calls, bandwidth
    metric_value DECIMAL(15, 2) NOT NULL,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_tenant_usage_tenant ON tenant_usage(tenant_id, recorded_at);
CREATE INDEX idx_tenant_usage_metric ON tenant_usage(metric_type, recorded_at);

-- Audit logs (cross-tenant)
CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    tenant_id INTEGER REFERENCES tenants(id) ON DELETE SET NULL,
    user_id INTEGER,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    ip_address INET,
    user_agent TEXT,
    request_data JSONB,
    response_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_logs_tenant ON audit_logs(tenant_id, created_at);
CREATE INDEX idx_audit_logs_action ON audit_logs(action, created_at);

-- Tenant migrations (for scaling)
CREATE TABLE tenant_migrations (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER REFERENCES tenants(id),
    from_instance VARCHAR(100) NOT NULL,
    to_instance VARCHAR(100) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'failed', 'rolled_back')),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    metadata JSONB DEFAULT '{}'
);

-- Function to create tenant schema
CREATE OR REPLACE FUNCTION create_tenant_schema(tenant_schema_name VARCHAR)
RETURNS VOID AS $$
BEGIN
    -- Create schema
    EXECUTE format('CREATE SCHEMA IF NOT EXISTS %I', tenant_schema_name);

    -- Create users table in tenant schema
    EXECUTE format('
        CREATE TABLE %I.users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) NOT NULL UNIQUE,
            first_name VARCHAR(100),
            last_name VARCHAR(100),
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(50) DEFAULT ''user'',
            is_active BOOLEAN DEFAULT true,
            last_login TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )', tenant_schema_name);

    -- Create projects table
    EXECUTE format('
        CREATE TABLE %I.projects (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            owner_id INTEGER REFERENCES %I.users(id),
            status VARCHAR(20) DEFAULT ''active'',
            settings JSONB DEFAULT ''{}'',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )', tenant_schema_name, tenant_schema_name);

    -- Create tasks table
    EXECUTE format('
        CREATE TABLE %I.tasks (
            id SERIAL PRIMARY KEY,
            project_id INTEGER REFERENCES %I.projects(id) ON DELETE CASCADE,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            assigned_to INTEGER REFERENCES %I.users(id),
            status VARCHAR(20) DEFAULT ''open'',
            priority VARCHAR(20) DEFAULT ''medium'',
            due_date DATE,
            completed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )', tenant_schema_name, tenant_schema_name, tenant_schema_name);

    -- Create indexes
    EXECUTE format('CREATE INDEX idx_%I_users_email ON %I.users(email)',
        tenant_schema_name, tenant_schema_name);
    EXECUTE format('CREATE INDEX idx_%I_projects_owner ON %I.projects(owner_id)',
        tenant_schema_name, tenant_schema_name);
    EXECUTE format('CREATE INDEX idx_%I_tasks_project ON %I.tasks(project_id)',
        tenant_schema_name, tenant_schema_name);
    EXECUTE format('CREATE INDEX idx_%I_tasks_assigned ON %I.tasks(assigned_to)',
        tenant_schema_name, tenant_schema_name);

END;
$$ LANGUAGE plpgsql;

-- Function to provision new tenant
CREATE OR REPLACE FUNCTION provision_tenant(
    p_tenant_key VARCHAR,
    p_company_name VARCHAR,
    p_subdomain VARCHAR,
    p_plan_id INTEGER,
    p_admin_email VARCHAR,
    p_admin_password VARCHAR
)
RETURNS INTEGER AS $$
DECLARE
    v_tenant_id INTEGER;
    v_schema_name VARCHAR(63);
    v_password_hash VARCHAR(255);
BEGIN
    -- Generate schema name
    v_schema_name := 'tenant_' || p_tenant_key;

    -- Hash password
    v_password_hash := crypt(p_admin_password, gen_salt('bf'));

    -- Create tenant record
    INSERT INTO tenants (tenant_key, company_name, subdomain, plan_id, schema_name, status)
    VALUES (p_tenant_key, p_company_name, p_subdomain, p_plan_id, v_schema_name, 'trial')
    RETURNING id INTO v_tenant_id;

    -- Set trial period (30 days)
    UPDATE tenants
    SET trial_ends_at = CURRENT_TIMESTAMP + INTERVAL '30 days'
    WHERE id = v_tenant_id;

    -- Create schema and tables
    PERFORM create_tenant_schema(v_schema_name);

    -- Create admin user
    INSERT INTO tenant_admins (tenant_id, email, password_hash, is_primary)
    VALUES (v_tenant_id, p_admin_email, v_password_hash, true);

    -- Log provisioning
    INSERT INTO audit_logs (tenant_id, action, resource_type, resource_id)
    VALUES (v_tenant_id, 'tenant_provisioned', 'tenant', v_tenant_id::VARCHAR);

    RETURN v_tenant_id;
END;
$$ LANGUAGE plpgsql;

-- Function to update tenant usage
CREATE OR REPLACE FUNCTION update_tenant_usage(
    p_tenant_id INTEGER,
    p_metric_type VARCHAR,
    p_value DECIMAL
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO tenant_usage (tenant_id, metric_type, metric_value)
    VALUES (p_tenant_id, p_metric_type, p_value);

    -- Update current values in tenants table
    IF p_metric_type = 'users' THEN
        UPDATE tenants SET current_users = p_value WHERE id = p_tenant_id;
    ELSIF p_metric_type = 'storage' THEN
        UPDATE tenants SET current_storage_gb = p_value WHERE id = p_tenant_id;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- View for tenant resource usage
CREATE VIEW tenant_resource_summary AS
SELECT
    t.id,
    t.tenant_key,
    t.company_name,
    t.status,
    p.name as plan_name,
    t.current_users,
    t.max_users,
    t.current_storage_gb,
    t.max_storage_gb,
    ROUND((t.current_users::DECIMAL / NULLIF(t.max_users, 0)) * 100, 2) as user_usage_percent,
    ROUND((t.current_storage_gb / NULLIF(t.max_storage_gb, 0)) * 100, 2) as storage_usage_percent,
    t.created_at,
    t.trial_ends_at,
    CASE
        WHEN t.status = 'trial' AND t.trial_ends_at < CURRENT_TIMESTAMP THEN 'expired'
        WHEN t.current_users >= t.max_users THEN 'user_limit_reached'
        WHEN t.current_storage_gb >= t.max_storage_gb THEN 'storage_limit_reached'
        ELSE 'ok'
    END as resource_status
FROM tenants t
JOIN plans p ON t.plan_id = p.id;

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO admin;
