from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from app.api.v1 import routes_health, routes_users, routes_products,routes_auth, routes_s3, routes_orders
from app.core.config import settings
from app.db.pg import wait_for_postgres, close_engine
from app.db.mongo import get_mongo_client, close_mongo_client, init_indexes
import logging

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code to run on startup
    try:
        await wait_for_postgres()
        await init_indexes()
        client = get_mongo_client()
        await client.admin.command("ping")
        logger.info("Database connections established.")
    except Exception as exc:
        logger.exception("Failed to connect to databases on startup: %s", exc)
        raise

    yield # The application runs here

    # Code to run on shutdown
    await close_engine()
    close_mongo_client()
    logger.info("Database connections closed.")

app = FastAPI(title=settings.PROJECT_NAME, version="1.0", lifespan=lifespan)


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# HTTPS redirect
if settings.HTTPS_ONLY:
    app.add_middleware(HTTPSRedirectMiddleware)
# Routers
app.include_router(routes_health.router, prefix="/api/v1/health", tags=["health"])
app.include_router(routes_auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(routes_users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(routes_products.router, prefix="/api/v1/products", tags=["products"])
app.include_router(routes_orders.router, prefix="/api/v1/orders", tags=["orders"])
app.include_router(routes_s3.router, prefix="/api/v1/s3", tags=["s3"])


@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}
