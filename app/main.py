from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app.api.v1 import onboarding, login, user, query  # All routers

app = FastAPI(
    title="MIIHA Health Chatbot API",
    version="1.0.0",
    description="Backend for personalized health assistant"
)

# ✅ CORS middleware (update allowed origins if needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⬅️ You can change to ["https://your-flutter.web.app"] later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Custom OpenAPI with bearer token support
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

# ✅ API routes
app.include_router(onboarding.router, prefix="/api/v1")
app.include_router(login.router, prefix="/api/v1")
app.include_router(user.router, prefix="/api/v1")
app.include_router(query.router, prefix="/api/v1")
