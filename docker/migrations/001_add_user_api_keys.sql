-- Migration: Add user API key support
-- Date: 2025-12-22
-- Description: Adds user_api_key and user_api_key_expiry columns to users table

ALTER TABLE users 
ADD COLUMN user_api_key character varying(64),
ADD COLUMN user_api_key_expiry timestamp with time zone;

-- Create index for faster API key lookups
CREATE INDEX idx_users_api_key ON users(user_api_key) WHERE user_api_key IS NOT NULL;

COMMENT ON COLUMN users.user_api_key IS 'User-specific API key for external app authentication';
COMMENT ON COLUMN users.user_api_key_expiry IS 'Expiry timestamp for user API key';
