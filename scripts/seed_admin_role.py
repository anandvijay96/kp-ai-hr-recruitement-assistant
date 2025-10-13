"""Seed admin role with user management permissions"""
import sqlite3
import json
import os
from datetime import datetime

db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'hr_recruitment.db')

# Admin role permissions - comprehensive set for user management
ADMIN_PERMISSIONS = [
    # User Management
    "user.manage",
    "user.create",
    "user.edit",
    "user.delete",
    "user.deactivate",
    "user.reactivate",
    "user.role_change",

    # Job Management
    "job.create",
    "job.edit",
    "job.delete",
    "job.publish",
    "job.close",
    "job.reopen",
    "job.view_all",

    # Candidate Management
    "resume.upload",
    "resume.rate",
    "resume.approve",
    "candidate.hire",
    "candidate.view_all",

    # Analytics & Reporting
    "analytics.view_all",
    "data.export",
    "audit.view",

    # System Administration
    "settings.manage",
    "system.configure",
    "audit.view_all"
]

print("="*60)
print("🔐 Seeding Admin Role")
print("="*60)

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if admin role already exists
    cursor.execute("SELECT id, name FROM user_roles WHERE name = ?", ("admin",))
    existing_role = cursor.fetchone()

    if existing_role:
        role_id, role_name = existing_role
        print(f"⚠️  Admin role already exists with ID: {role_id}")
        print("   Updating permissions...")

        # Update existing role permissions
        cursor.execute("""
            UPDATE user_roles
            SET permissions = ?, updated_at = ?
            WHERE name = ?
        """, (json.dumps(ADMIN_PERMISSIONS), datetime.now().isoformat(), "admin"))

        conn.commit()
        print(f"✅ Admin role permissions updated ({len(ADMIN_PERMISSIONS)} permissions)")
    else:
        # Create new admin role
        import uuid
        role_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        cursor.execute("""
            INSERT INTO user_roles (
                id, name, display_name, description, permissions,
                is_system_role, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            role_id,
            "admin",
            "Administrator",
            "Full system administrator with complete access to all features",
            json.dumps(ADMIN_PERMISSIONS),
            True,  # is_system_role
            now,
            now
        ))

        conn.commit()
        print(f"✅ Admin role created with ID: {role_id}")
        print(f"   Permissions: {len(ADMIN_PERMISSIONS)} permissions")

    # Verify the role exists and has permissions
    cursor.execute("SELECT permissions FROM user_roles WHERE name = ?", ("admin",))
    role_data = cursor.fetchone()

    if role_data:
        permissions = json.loads(role_data[0] or '[]')
        print("\n📋 Admin Role Permissions:")
        for i, perm in enumerate(permissions, 1):
            print(f"   {i:2d}. {perm}")

    conn.close()

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("🎯 Next Steps:")
print("1. Restart your server")
print("2. Refresh the Users page")
print("3. Try creating a user again")
print("="*60)
