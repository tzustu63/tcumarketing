-- Add country column to tasks table
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS country VARCHAR(2) NOT NULL DEFAULT 'ID';

-- Add comment
COMMENT ON COLUMN tasks.country IS '國家代碼';
