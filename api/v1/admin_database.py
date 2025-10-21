"""
Admin Database Management API
Developer-only endpoints for database management
"""
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
import logging

from core.database import get_db
from core.auth import get_current_user
from models.database import User
from services.password_service import PasswordService

router = APIRouter(prefix="/admin/database", tags=["Admin Database"])
logger = logging.getLogger(__name__)


def require_admin(current_user: User = Depends(get_current_user)):
    """Require admin role"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@router.get("/tables")
async def list_tables(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """List all database tables"""
    try:
        result = await db.execute(text("""
            SELECT table_name, 
                   (SELECT COUNT(*) FROM information_schema.columns 
                    WHERE table_name = t.table_name) as column_count
            FROM information_schema.tables t
            WHERE table_schema = 'public'
            ORDER BY table_name
        """))
        
        tables = []
        for row in result.fetchall():
            tables.append({
                "name": row[0],
                "column_count": row[1]
            })
        
        return {"success": True, "tables": tables}
        
    except Exception as e:
        logger.error(f"Error listing tables: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tables/{table_name}/schema")
async def get_table_schema(
    table_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get schema for a specific table"""
    try:
        result = await db.execute(text("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = :table_name
            ORDER BY ordinal_position
        """), {"table_name": table_name})
        
        columns = []
        for row in result.fetchall():
            columns.append({
                "name": row[0],
                "type": row[1],
                "nullable": row[2] == 'YES',
                "default": row[3]
            })
        
        return {"success": True, "table": table_name, "columns": columns}
        
    except Exception as e:
        logger.error(f"Error getting schema: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query")
async def execute_query(
    query: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Execute a SQL query (SELECT only for safety)"""
    try:
        # Only allow SELECT queries for safety
        if not query.strip().upper().startswith("SELECT"):
            raise HTTPException(
                status_code=400, 
                detail="Only SELECT queries are allowed for safety"
            )
        
        result = await db.execute(text(query))
        
        # Get column names
        columns = list(result.keys()) if result.keys() else []
        
        # Get rows
        rows = []
        for row in result.fetchall():
            rows.append(dict(zip(columns, row)))
        
        return {
            "success": True,
            "columns": columns,
            "rows": rows,
            "row_count": len(rows)
        }
        
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users")
async def list_all_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """List all users in the system"""
    try:
        result = await db.execute(
            select(User).order_by(User.created_at.desc())
        )
        users = result.scalars().all()
        
        user_list = []
        for user in users:
            user_list.append({
                "id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "role": user.role,
                "is_active": user.is_active,
                "email_verified": user.email_verified,
                "status": user.status,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "login_count": user.login_count
            })
        
        return {"success": True, "users": user_list, "total": len(user_list)}
        
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: str,
    new_password: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Reset a user's password"""
    try:
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Hash new password
        password_service = PasswordService()
        user.password_hash = password_service.hash_password(new_password)
        user.is_active = True
        user.email_verified = True
        user.failed_login_attempts = 0
        user.account_locked_until = None
        
        await db.commit()
        
        return {
            "success": True,
            "message": f"Password reset for {user.email}",
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting password: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/users/{user_id}/toggle-active")
async def toggle_user_active(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Toggle user active status"""
    try:
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user.is_active = not user.is_active
        await db.commit()
        
        return {
            "success": True,
            "message": f"User {'activated' if user.is_active else 'deactivated'}",
            "is_active": user.is_active
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling user: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_database_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get database statistics"""
    try:
        # Get table counts
        stats = {}
        
        tables = ["users", "candidates", "resumes", "jobs", "user_activity_log", "interviews"]
        
        for table in tables:
            result = await db.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            stats[table] = count
        
        return {"success": True, "stats": stats}
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
