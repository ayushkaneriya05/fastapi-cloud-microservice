from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from app.api.v1 import routes_health, routes_users, routes_products,routes_auth, routes_s3, routes_orders
from app.core.config import settings
from app.db.pg import wait_for_postgres, close_engine
from app.db.mongo import get_mongo_client, close_mongo_client, init_indexes
import logging

logger = logging.getLogger(__name__)

app = FastAPI(title=settings.PROJECT_NAME, version="1.0")

@app.on_event("startup")
async def on_startup():
    # wait for postgres to be accepting connections (retries included)
    try:
        await wait_for_postgres()
        await init_indexes()
    except Exception as exc:
        logger.exception("Postgres did not become available: %s", exc)
        raise

    # warm up mongo client (optional)
    try:
        client = get_mongo_client()
        # force server selection (will raise on failure)
        await client.admin.command("ping")
    except Exception as exc:
        logger.exception("MongoDB did not become available: %s", exc)
        raise

@app.on_event("shutdown")
async def on_shutdown():
    await close_engine()
    close_mongo_client()

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
