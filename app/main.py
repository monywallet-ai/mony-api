from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

from app.api.main import api_router
from app.core.logging import general_logger, setup_logging
from app.core.middleware import RequestLoggingMiddleware
from app.settings import settings
from app.auth import get_docs_auth_dependency


def custom_generate_unique_id(route: APIRoute) -> str:
    if route.tags:
        return f"{route.tags[0]}-{route.name}"
    return route.name


# Get the docs authentication dependency
docs_auth_dependency = get_docs_auth_dependency()

# Configure FastAPI with conditional docs authentication
app_config = {
    "title": settings.PROJECT_NAME,
    "version": settings.API_VERSION,
    "description": f"Mony API - Environment: {settings.ENVIRONMENT}",
    "generate_unique_id_function": custom_generate_unique_id,
    "lifespan": None,
}

# Configure docs URLs based on authentication
if settings.ENABLE_DOCS_AUTH:
    # Disable default docs, we'll create custom authenticated endpoints
    app_config.update(
        {
            "docs_url": None,
            "openapi_url": None,
            "redoc_url": None,
        }
    )
else:
    # Enable default docs without authentication
    app_config.update(
        {
            "docs_url": "/docs",
            "openapi_url": "/openapi.json",
            "redoc_url": "/redoc",
        }
    )


# Set up logging before creating the FastAPI app
setup_logging(
    log_level=settings.LOG_LEVEL,
    environment=settings.ENVIRONMENT,
    json_logs=settings.JSON_LOGS,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    Handles startup and shutdown events.
    """
    general_logger.info(
        "application_starting",
        environment=settings.ENVIRONMENT,
        log_level=settings.LOG_LEVEL,
        json_logs=settings.JSON_LOGS,
    )

    # Add startup tasks here
    # e.g., database connections, cache initialization, etc.

    try:
        yield
    finally:
        # Shutdown
        general_logger.info("application_shutting_down")

        # Add shutdown tasks here
        # e.g., close database connections, cleanup resources, etc.


app_config["lifespan"] = lifespan

app = FastAPI(**app_config)


# Custom authenticated documentation endpoints
if settings.ENABLE_DOCS_AUTH:

    @app.get("/openapi.json", include_in_schema=False)
    async def get_openapi_endpoint(_: bool = Depends(docs_auth_dependency)):
        return get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )

    @app.get("/docs", include_in_schema=False)
    async def get_documentation(_: bool = Depends(docs_auth_dependency)):
        return get_swagger_ui_html(
            openapi_url="/openapi.json",
            title=f"{app.title} - Documentation",
        )

    @app.get("/redoc", include_in_schema=False)
    async def get_redoc_documentation(_: bool = Depends(docs_auth_dependency)):
        from fastapi.openapi.docs import get_redoc_html

        return get_redoc_html(
            openapi_url="/openapi.json",
            title=f"{app.title} - ReDoc",
        )


@app.get("/health")
async def health_check():
    import os
    import sys

    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "version": settings.API_VERSION.lstrip("/"),
        "project": settings.PROJECT_NAME,
        "debug": settings.DEBUG,
        "workers": os.environ.get("WORKERS", "auto-detected"),
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "docs_auth_enabled": settings.ENABLE_DOCS_AUTH,
        "docs_endpoints": {
            "swagger": (
                "/docs"
                if not settings.ENABLE_DOCS_AUTH or settings.DEBUG
                else "/docs (authentication required)"
            ),
            "redoc": (
                "/redoc"
                if not settings.ENABLE_DOCS_AUTH or settings.DEBUG
                else "/redoc (authentication required)"
            ),
            "openapi": (
                "/openapi.json"
                if not settings.ENABLE_DOCS_AUTH or settings.DEBUG
                else "/openapi.json (authentication required)"
            ),
        },
    }


@app.get("/docs-info")
async def docs_info():
    """Information about API documentation access"""
    return {
        "docs_authentication_enabled": settings.ENABLE_DOCS_AUTH,
        "environment": settings.ENVIRONMENT,
        "message": (
            "Documentation requires HTTP Basic Authentication"
            if settings.ENABLE_DOCS_AUTH
            else "Documentation is publicly accessible"
        ),
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "openapi_url": "/openapi.json",
        "credentials_note": (
            "Contact your administrator for documentation credentials"
            if settings.ENABLE_DOCS_AUTH
            else None
        ),
    }


@app.get("/debug/config-sources")
async def config_sources():
    """Debug endpoint - shows where each configuration comes from"""
    if not settings.DEBUG:
        return {"error": "Debug mode is disabled"}

    config_info = settings.get_config_source_info()

    # Add docs authentication info to debug output
    config_info.update(
        {
            "docs_authentication": {
                "enabled": settings.ENABLE_DOCS_AUTH,
                "username_set": bool(settings.DOCS_USERNAME),
                "password_set": bool(settings.DOCS_PASSWORD),
                "auto_enabled_for_production": settings.ENVIRONMENT == "production",
            }
        }
    )

    return {
        "config_sources": config_info,
        "note": "This endpoint is only available in debug mode",
    }


@app.get("/debug/dependencies")
async def dependencies_info():
    """Debug endpoint - shows installed package versions"""
    if not settings.DEBUG:
        return {"error": "Debug mode is disabled"}

    import subprocess
    import sys

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "list", "--format=json"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            import json

            packages = json.loads(result.stdout)
            return {
                "installed_packages": packages,
                "total_packages": len(packages),
                "python_version": sys.version,
                "note": "This endpoint is only available in debug mode",
            }
        else:
            return {"error": "Could not retrieve package information"}
    except Exception as e:
        return {"error": f"Error retrieving dependencies: {str(e)}"}


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.all_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request logging middleware
if settings.ENABLE_REQUEST_LOGGING:
    app.add_middleware(
        RequestLoggingMiddleware, exclude_paths=settings.REQUEST_LOG_EXCLUDE_PATHS
    )

app.include_router(api_router, prefix=settings.API_VERSION)
