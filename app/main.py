from fastapi import FastAPI
from app.api.v1 import onboarding, login, user, query  # All routers
from fastapi.openapi.utils import get_openapi

app = FastAPI(
    title="MIIHA Health Chatbot API",
    version="1.0.0",
    description="Backend for personalized health assistant"
)
# Optional override: custom OpenAPI schema to support bearer token manually
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
            "bearerFormat": "JWT"
        }
    }
    for path in openapi_schema["paths"].values():
        for method in path.values():
            method["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Include routers
app.include_router(onboarding.router, prefix="/api/v1")
app.include_router(login.router, prefix="/api/v1")
app.include_router(user.router, prefix="/api/v1")
app.include_router(query.router, prefix="/api/v1")   # <-- Must have
