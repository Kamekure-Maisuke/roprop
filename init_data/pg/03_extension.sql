CREATE EXTENSION IF NOT EXISTS pgroonga;

-- 全文検索用インデックス
CREATE INDEX IF NOT EXISTS pgroonga_pcs_idx ON pcs USING pgroonga ((ARRAY[name, model, serial_number]));
CREATE INDEX IF NOT EXISTS pgroonga_employees_idx ON employees USING pgroonga ((ARRAY[name, email]));
CREATE INDEX IF NOT EXISTS pgroonga_blog_posts_idx ON blog_posts USING pgroonga ((ARRAY[title, content]));