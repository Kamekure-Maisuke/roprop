-- Add resignation_date and transfer_date columns to employees table
ALTER TABLE employees
ADD COLUMN IF NOT EXISTS resignation_date DATE,
ADD COLUMN IF NOT EXISTS transfer_date DATE;

-- Create index for efficient querying of upcoming resignations and transfers
CREATE INDEX IF NOT EXISTS idx_employees_resignation_date ON employees(resignation_date);
CREATE INDEX IF NOT EXISTS idx_employees_transfer_date ON employees(transfer_date);
