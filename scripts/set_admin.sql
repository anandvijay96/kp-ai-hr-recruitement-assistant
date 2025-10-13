-- Set Kartik@kloudportal.com as admin
-- Run this script to update the user role

-- First, check if user exists
SELECT id, email, full_name, role FROM users WHERE email = 'Kartik@kloudportal.com';

-- Update user role to admin
UPDATE users 
SET role = 'admin' 
WHERE email = 'Kartik@kloudportal.com';

-- Verify the update
SELECT id, email, full_name, role FROM users WHERE email = 'Kartik@kloudportal.com';

-- Show all users and their roles
SELECT email, full_name, role, is_active FROM users ORDER BY email;
