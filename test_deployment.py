#!/usr/bin/env python3
"""
Test script to verify all components work before deployment to Azure
"""
import sys
import os

def test_imports():
    """Test all critical imports"""
    print("🧪 Testing critical imports...")
    
    try:
        import fastapi
        print(f"✅ FastAPI {fastapi.__version__}")
    except Exception as e:
        print(f"❌ FastAPI import failed: {e}")
        return False
    
    try:
        import sqlalchemy
        print(f"✅ SQLAlchemy {sqlalchemy.__version__}")
    except Exception as e:
        print(f"❌ SQLAlchemy import failed: {e}")
        return False
    
    try:
        import psycopg2
        print(f"✅ psycopg2 {psycopg2.__version__}")
        print(f"✅ psycopg2 paramstyle: {psycopg2.paramstyle}")
    except Exception as e:
        print(f"❌ psycopg2 test failed: {e}")
        return False
    
    return True

def test_settings():
    """Test settings configuration"""
    print("\n⚙️  Testing settings...")
    
    try:
        from app.settings import settings
        print(f"✅ Settings loaded successfully")
        print(f"   Environment: {settings.ENVIRONMENT}")
        print(f"   Debug: {settings.DEBUG}")
        print(f"   Docs Auth: {settings.ENABLE_DOCS_AUTH}")
        return True
    except Exception as e:
        print(f"❌ Settings test failed: {e}")
        return False

def test_database():
    """Test database configuration"""
    print("\n🗄️  Testing database...")
    
    try:
        from app.database import engine
        print("✅ Database engine created successfully")
        return True
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        print("   Make sure PostgreSQL is running and credentials are correct")
        return False

def test_fastapi_app():
    """Test FastAPI application"""
    print("\n🚀 Testing FastAPI application...")
    
    try:
        from app.main import app
        print("✅ FastAPI app loaded successfully")
        print(f"   Title: {app.title}")
        print(f"   Version: {app.version}")
        return True
    except Exception as e:
        print(f"❌ FastAPI app test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🏃‍♂️ Running pre-deployment tests...\n")
    
    tests = [
        ("Imports", test_imports),
        ("Settings", test_settings),
        ("Database", test_database),
        ("FastAPI App", test_fastapi_app),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"⚠️  {test_name} test had issues")
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Ready for deployment.")
        return 0
    else:
        print("⚠️  Some tests failed. Review issues before deploying.")
        return 1

if __name__ == "__main__":
    sys.exit(main())