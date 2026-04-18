from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer

SECRET_KEY = "super-secret-key"
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# PASSWORDS
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)

# JWT
def create_access_token(user_id: int):
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str):
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

# GET USER
security = HTTPBearer()

async def get_current_user(
    request: Request,
    credentials=Depends(security),
):
    token = credentials.credentials

    try:
        payload = decode_token(token)
        user_id = payload.get("user_id")
    except JWTError:
        raise HTTPException(401, "Invalid token")

    pool = request.app.state.db_pool

    async with pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT * FROM users WHERE id=$1 AND is_active=TRUE",
            user_id
        )

    if not user:
        raise HTTPException(401, "User not found")
    print("TOKEN:", token)
    print("PAYLOAD:", payload)
    print("USER_ID:", user_id)
    return user
