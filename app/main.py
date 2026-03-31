import logging

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from app.api.v1 import login, onboarding, query, user
from app.db.mongodb import check_connection
from app.utils.logger import get_logger

# Root logger configuration (applies to all modules)
logging.basicConfig(level=logging.INFO)
logger = get_logger(__name__)

app = FastAPI(
    title="MIIHA Health Chatbot API",
    version="1.0.0",
    description="Backend for personalized health assistant",
)


@app.on_event("startup")
async def startup_event() -> None:
    logger.info("Starting MIIHA Health Chatbot API…")
    connected = await check_connection()
    if not connected:
        logger.warning("MongoDB could not be reached at startup — check MONGODB_URI")
    logger.info("API startup complete")


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    for path in openapi_schema["paths"].values():
        for method in path.values():
            method["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

app.include_router(onboarding.router, prefix="/api/v1")
app.include_router(login.router, prefix="/api/v1")
app.include_router(user.router, prefix="/api/v1")
app.include_router(query.router, prefix="/api/v1")
