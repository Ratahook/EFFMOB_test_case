from fastapi import APIRouter, Depends, HTTPException, Request
from Roles.dependency import require_permission
from typing import Dict
from Authorizer.encript import get_current_user

router = APIRouter()

@router.get("/user/{user_id}")
async def get_user(
    user_id: int,
    user=Depends(require_permission("read_profile")),
    request: Request = None
):
    pool = request.app.state.db_pool

    async with pool.acquire() as conn:
        target = await conn.fetchrow(
            "SELECT id, email, first_name, last_name FROM users WHERE id=$1",
            user_id
        )

    if not target:
        raise HTTPException(404, "User not found")

    return dict(target)

@router.put("/user/{user_id}")
async def update_user(
    user_id: int,
    data: Dict,
    user=Depends(get_current_user),
    request: Request = None
):
    pool = request.app.state.db_pool

    is_owner = user["id"] == user_id

    if not is_owner:
        async with pool.acquire() as conn:
            allowed = await conn.fetchrow("""
                SELECT 1
                FROM user_roles ur
                JOIN role_permissions rp ON ur.role_id = rp.role_id
                JOIN permissions p ON rp.permission_id = p.id
                WHERE ur.user_id = $1 AND p.name = 'edit_profile'
            """, user["id"])

        if not allowed:
            raise HTTPException(403, "Forbidden")

    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE users
            SET first_name=$1, last_name=$2
            WHERE id=$3
        """,
        data.get("first_name"),
        data.get("last_name"),
        user_id
        )

    return {"message": "User updated"}

@router.delete("/user/{user_id}")
async def delete_user(
    user_id: int,
    user=Depends(get_current_user),
    request: Request = None
):
    pool = request.app.state.db_pool

    is_owner = user["id"] == user_id

    if not is_owner:
        async with pool.acquire() as conn:
            allowed = await conn.fetchrow("""
                SELECT 1
                FROM user_roles ur
                JOIN role_permissions rp ON ur.role_id = rp.role_id
                JOIN permissions p ON rp.permission_id = p.id
                WHERE ur.user_id = $1 AND p.name = 'delete_user'
            """, user["id"])

        if not allowed:
            raise HTTPException(403, "Forbidden")

    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE users
            SET is_active = FALSE
            WHERE id=$1
        """, user_id)

    return {"message": "User deactivated"}