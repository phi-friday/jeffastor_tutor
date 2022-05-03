from sqlalchemy.engine.url import URL
from starlette.config import Config
from starlette.datastructures import Secret

config = Config(".env")

PROJECT_NAME = "jeffastor_tutor"
VERSION = "1.0.0"
API_PREFIX = "/api"
TOKEN_PREFIX = API_PREFIX + "/token"

TESTING = config("TESTING", cast=bool, default=False)

SECRET_KEY = config("SECRET_KEY", cast=Secret, default="CHANGEME")

POSTGRES_USER = config("POSTGRES_USER", cast=str)
POSTGRES_PASSWORD = config("POSTGRES_PASSWORD", cast=Secret)
POSTGRES_SERVER = config("POSTGRES_SERVER", cast=str, default="db")
POSTGRES_PORT = config("POSTGRES_PORT", cast=int, default=5432)
POSTGRES_DB = config("POSTGRES_DB", cast=str)

DATABASE_URL = config(
    "DATABASE_URL",
    cast=str,
    default=URL.create(
        drivername="postgresql+asyncpg",
        username=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        host=POSTGRES_SERVER,
        port=POSTGRES_PORT,
        database=POSTGRES_DB,
    ).render_as_string(hide_password=False),
)
