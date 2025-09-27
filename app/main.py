import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute

from app.api.main import api_router
from app.settings import settings


def custom_generate_unique_id(route: APIRoute) -> str:
    if route.tags:
        return f"{route.tags[0]}-{route.name}"
    return route.name


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.API_VERSION,
    description="Mony API",
    docs_url="/docs",
    openapi_url="/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
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
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    }

@app.get("/debug/config-sources")
async def config_sources():
    """Debug endpoint - shows where each configuration comes from"""
    if not settings.DEBUG:
        return {"error": "Debug mode is disabled"}
    
    return {
        "config_sources": settings.get_config_source_info(),
        "note": "This endpoint is only available in debug mode"
    }

@app.get("/debug/dependencies")
async def dependencies_info():
    """Debug endpoint - shows installed package versions"""
    if not settings.DEBUG:
        return {"error": "Debug mode is disabled"}
    
    import subprocess
    import sys
    
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "list", "--format=json"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            import json
            packages = json.loads(result.stdout)
            return {
                "installed_packages": packages,
                "total_packages": len(packages),
                "python_version": sys.version,
                "note": "This endpoint is only available in debug mode"
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

app.include_router(api_router, prefix=settings.API_VERSION)
