from fastapi import APIRouter, Depends, HTTPException, Request
from Roles.dependency import require_permission

router = APIRouter()

@router.post("/add-role")
async def add_role(
    user_id: int,
    role_name: str,
    request: Request,
    admin=Depends(require_permission("delete_user"))
):
    pool = request.app.state.db_pool

    async with pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT id FROM users WHERE id=$1",
            user_id
        )
        if not user:
            raise HTTPException(404, "User not found")

        role = await conn.fetchrow(
            "SELECT id FROM roles WHERE name=$1",
            role_name
        )
        if not role:
            raise HTTPException(404, "Role not found")

        exists = await conn.fetchrow("""
            SELECT 1 FROM user_roles
            WHERE user_id=$1 AND role_id=$2
        """, user_id, role["id"])

        if exists:
            raise HTTPException(400, "User already has this role")

        await conn.execute("""
            INSERT INTO user_roles (user_id, role_id)
            VALUES ($1, $2)
        """, user_id, role["id"])

    return {"message": "Role added"}


@router.post("/test-make-admin")
async def make_admin(user_id: int, request: Request):
    pool = request.app.state.db_pool

    async with pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT id FROM users WHERE id=$1",
            user_id
        )
        if not user:
            raise HTTPException(404, "User not found")

        role = await conn.fetchrow(
            "SELECT id FROM roles WHERE name='admin'"
        )
        if not role:
            raise HTTPException(500, "Admin role not found")

        exists = await conn.fetchrow("""
            SELECT 1 FROM user_roles
            WHERE user_id=$1 AND role_id=$2
        """, user_id, role["id"])

        if exists:
            raise HTTPException(400, "User already admin")

        await conn.execute("""
            INSERT INTO user_roles (user_id, role_id)
            VALUES ($1, $2)
        """, user_id, role["id"])

    return {"message": "User is now admin"}