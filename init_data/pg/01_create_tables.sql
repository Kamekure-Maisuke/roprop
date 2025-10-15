-- Create departments table
CREATE TABLE IF NOT EXISTS departments (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);

-- Create employees table
CREATE TABLE IF NOT EXISTS employees (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    department_id UUID REFERENCES departments(id) ON DELETE SET NULL,
    profile_image BYTEA
);

-- Create pcs table
CREATE TABLE IF NOT EXISTS pcs (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    model VARCHAR(255) NOT NULL,
    serial_number VARCHAR(255) NOT NULL UNIQUE,
    assigned_to UUID REFERENCES employees(id) ON DELETE SET NULL
);

-- Create pc_assignment_histories table
CREATE TABLE IF NOT EXISTS pc_assignment_histories (
    id UUID PRIMARY KEY,
    pc_id UUID NOT NULL REFERENCES pcs(id) ON DELETE CASCADE,
    employee_id UUID REFERENCES employees(id) ON DELETE SET NULL,
    assigned_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    notes TEXT DEFAULT ''
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_employees_department_id ON employees(department_id);
CREATE INDEX IF NOT EXISTS idx_pcs_assigned_to ON pcs(assigned_to);
CREATE INDEX IF NOT EXISTS idx_pc_assignment_histories_pc_id ON pc_assignment_histories(pc_id);
CREATE INDEX IF NOT EXISTS idx_pc_assignment_histories_employee_id ON pc_assignment_histories(employee_id);
