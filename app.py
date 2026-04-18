import asyncpg
from contextlib import asynccontextmanager
from config import settings
from fastapi import FastAPI
from DB.Base import bd_activate, set_testdata
from Routers.app_authorize import router as auth_router
from Routers.admin import router as admin_router
from Routers.account_actions import router as actions_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db_pool = await asyncpg.create_pool(
        database=settings.db_name,
        user=settings.db_user,
        password=settings.db_password,
        host=settings.db_host,
        port=settings.db_port
    )
    await bd_activate(app.state.db_pool)
    await set_testdata(app.state.db_pool)
    yield
    await app.state.db_pool.close()

app = FastAPI(lifespan=lifespan)

app.include_router(auth_router, prefix="/auth")
app.include_router(admin_router, prefix="/admin")
app.include_router(actions_router, prefix="/actions")
