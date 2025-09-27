#!/usr/bin/env python3
"""
Dependency verification script for Azure Web App deployment
Checks if critical dependencies are properly installed
"""
import sys
import importlib

def check_dependency(module_name, package_name=None):
    """Check if a dependency can be imported"""
    try:
        importlib.import_module(module_name)
        print(f"✅ {module_name} is available")
        return True
    except ImportError as e:
        print(f"❌ {module_name} is NOT available: {e}")
        if package_name:
            print(f"   Install with: pip install {package_name}")
        return False

def main():
    """Check all critical dependencies"""
    print("🔍 Checking critical dependencies...")
    
    critical_deps = [
        ("fastapi", "fastapi[standard]"),
        ("uvicorn", "uvicorn[standard]"),
        ("gunicorn", "gunicorn"),
        ("sqlalchemy", "sqlalchemy"),
        ("alembic", "alembic"),
        ("psycopg2", "psycopg2-binary"),
        ("websockets", "websockets"),
        ("pydantic", "pydantic"),
        ("pydantic_settings", "pydantic-settings"),
    ]
    
    optional_deps = [
        ("asyncpg", "asyncpg"),
        ("openai", "openai"),
        ("jose", "python-jose[cryptography]"),
        ("passlib", "passlib[bcrypt]"),
    ]
    
    critical_missing = []
    optional_missing = []
    
    print("\n📦 Critical Dependencies:")
    for module, package in critical_deps:
        if not check_dependency(module, package):
            critical_missing.append(package)
    
    print("\n🔧 Optional Dependencies:")
    for module, package in optional_deps:
        if not check_dependency(module, package):
            optional_missing.append(package)
    
    print("\n📋 Summary:")
    if not critical_missing:
        print("✅ All critical dependencies are available!")
    else:
        print(f"❌ Missing critical dependencies: {', '.join(critical_missing)}")
        print("🚨 Application may not start properly!")
    
    if optional_missing:
        print(f"⚠️  Missing optional dependencies: {', '.join(optional_missing)}")
        print("ℹ️  Some features may be limited.")
    
    # Return exit code based on critical dependencies
    return 0 if not critical_missing else 1

if __name__ == "__main__":
    sys.exit(main())