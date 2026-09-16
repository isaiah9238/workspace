ALTER TABLE tools ADD COLUMN category TEXT DEFAULT 'workspace';
ALTER TABLE tools ADD COLUMN usage_examples TEXT;
ALTER TABLE tools ADD COLUMN target_type TEXT DEFAULT 'python_function';
