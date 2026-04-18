from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict

from Authorizer.encript import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user
)
from Roles.dependency import require_permission

router = APIRouter()

@router.post("/register")
async def register(data: Dict, request: Request):
    pool = request.app.state.db_pool

    if data["password"] != data["password_repeat"]:
        raise HTTPException(400, "Passwords do not match")

    async with pool.acquire() as conn:
        existing = await conn.fetchrow(
            "SELECT id FROM users WHERE email=$1",
            data["email"]
        )

        if existing:
            raise HTTPException(400, "User already exists")

        await conn.execute("""
            INSERT INTO users (email, password_hash, first_name, last_name)
            VALUES ($1, $2, $3, $4)
        """,
        data["email"],
        hash_password(data["password"]),
        data.get("first_name"),
        data.get("last_name")
        )
        user = await conn.fetchrow(
            "SELECT id FROM users WHERE email=$1",
            data["email"]
        )
        await conn.execute("""
            INSERT INTO user_roles (user_id, role_id)
            SELECT $1, id FROM roles WHERE name='user'
        """, user["id"])

    return {"message": "User registered"}


@router.post("/login")
async def login(data: Dict, request: Request):
    pool = request.app.state.db_pool

    async with pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT * FROM users WHERE email=$1",
            data["email"]
        )

    if not user:
        raise HTTPException(401, "Invalid credentials")

    if not user["is_active"]:
        raise HTTPException(403, "User is inactive")

    if not verify_password(data["password"], user["password_hash"]):
        raise HTTPException(401, "Invalid credentials")

    token = create_access_token(user["id"])

    return {"access_token": token}


@router.get("/me")
async def me(user=Depends(require_permission("read_profile"))):
    return {
        "id": user["id"],
        "email": user["email"],
        "first_name": user["first_name"],
        "last_name": user["last_name"]
    }


@router.put("/me")
async def update_me(
    data: Dict,
    user=Depends(require_permission("edit_profile")),
    request: Request = None
):
    pool = request.app.state.db_pool

    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE users
            SET first_name=$1, last_name=$2
            WHERE id=$3
        """,
        data.get("first_name"),
        data.get("last_name"),
        user["id"]
        )

    return {"message": "Profile updated"}

@router.delete("/me")
async def delete_me(
    user=Depends(require_permission("delete_user")),
    request: Request = None
):
    pool = request.app.state.db_pool

    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE users
            SET is_active = FALSE
            WHERE id=$1
        """, user["id"])

    return {"message": "Account deactivated"}