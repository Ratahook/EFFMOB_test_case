from fastapi import Depends, HTTPException, Request
from Authorizer.encript import get_current_user

def require_permission(permission_name: str):
    async def permission_checker(
        request: Request,
        user=Depends(get_current_user)
    ):
        pool = request.app.state.db_pool

        async with pool.acquire() as conn:
            result = await conn.fetchrow("""
                SELECT 1
                FROM user_roles ur
                JOIN role_permissions rp ON ur.role_id = rp.role_id
                JOIN permissions p ON rp.permission_id = p.id
                WHERE ur.user_id = $1 AND p.name = $2
            """, user["id"], permission_name)

        if not result:
            raise HTTPException(403, "Forbidden")

        return user

    return permission_checker