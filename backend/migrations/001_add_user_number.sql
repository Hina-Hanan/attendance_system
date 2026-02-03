-- Run this once if your database was created before user_number was added.
-- Adds user_number column and optionally allows duplicate usernames.

-- 1. Add user_number column (nullable for existing rows)
ALTER TABLE users ADD COLUMN IF NOT EXISTS user_number INTEGER UNIQUE;

-- 2. Backfill user_number for existing users (1, 2, 3... by created_at)
WITH numbered AS (
  SELECT user_id, ROW_NUMBER() OVER (ORDER BY created_at) AS rn
  FROM users
  WHERE user_number IS NULL
)
UPDATE users SET user_number = numbered.rn
FROM numbered WHERE users.user_id = numbered.user_id;

-- 3. (Optional) Allow duplicate usernames - drop unique constraint on username.
--    Uncomment the line below if your table has unique on username and you want to allow same name for different people.
-- ALTER TABLE users DROP CONSTRAINT IF EXISTS users_username_key;
