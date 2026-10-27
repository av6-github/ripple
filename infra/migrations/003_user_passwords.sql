-- RIPPLE PostgreSQL Migration: 003_user_passwords.sql
-- Description: Adds secure password_hash column to app_user table for authentication and RBAC.

ALTER TABLE app_user ADD COLUMN IF NOT EXISTS password_hash TEXT;
