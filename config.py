from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    db_name: str = "db"
    db_user: str = "admin"
    db_password: str = "admin"
    db_host: str = "localhost"
    db_port: int = 5432

    class Config:
        env_file = ".env"


settings = Settings()