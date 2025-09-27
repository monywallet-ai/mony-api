# Azure Web App Deployment Troubleshooting

## Common Issues and Solutions

### 1. Directory not empty error (websockets)
**Error**: `OSError: [Errno 39] Directory not empty: '/home/site/wwwroot/.venv/lib/python3.12/site-packages/websockets/'`

**Solution**: 
- The startup.sh now automatically handles this by uninstalling conflicting packages before reinstalling
- If it persists, manually clean the virtual environment

### 2. psycopg2 ModuleNotFoundError
**Error**: `ModuleNotFoundError: No module named 'psycopg2'`

**Solutions implemented**:
- Removed conflicting `psycopg[binary]` dependency
- Added explicit psycopg2-binary installation with specific version
- Added verification step before running migrations
- Added fallback installation if verification fails

### 3. Virtual Environment Corruption
**Symptoms**: Random import errors, package not found errors

**Solution**: 
- startup.sh now detects and recreates corrupted virtual environments
- Uses corruption marker file to track issues

### 4. Database Migration Failures
**Solutions**:
- Added error handling for migrations - app continues if migrations fail
- Added check for migration files before attempting to run them
- Provides helpful error messages and next steps

## Monitoring and Debugging

### Dependency Check
Run the dependency verification script:
```bash
python check_dependencies.py
```

This will show you exactly which dependencies are missing or problematic.

### Manual Troubleshooting Commands

1. **Check Python environment**:
```bash
python -c "import sys; print(sys.path)"
python -c "import sys; print(sys.executable)"
```

2. **Verify database driver**:
```bash
python -c "import psycopg2; print('psycopg2 version:', psycopg2.__version__)"
```

3. **Test database connection**:
```bash
python -c "
from app.settings import settings
print('Database URL:', settings.DATABASE_URL)
"
```

4. **Check FastAPI imports**:
```bash
python -c "
from app.main import app
print('FastAPI app loaded successfully')
"
```

### Environment Variables for Azure

Ensure these are set in your Azure Web App configuration:

```bash
# Environment
ENVIRONMENT=production
DEBUG=false

# Database (set by Azure if using managed database)
DATABASE_URL=postgresql+psycopg2://user:pass@host:port/db
# OR individual components:
PG_SERVER=your-server.postgres.database.azure.com
PG_USER=your-username
PG_PASSWORD=your-password
PG_DB=your-database

# Documentation Security
ENABLE_DOCS_AUTH=true
DOCS_USERNAME=your-docs-username
DOCS_PASSWORD=your-secure-password

# API Keys
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret
OPEN_AI_SECRET_KEY=your-openai-key

# Azure Storage (optional)
AZURE_STORAGE_CONNECTION_STRING=your-storage-connection
AZURE_CONTAINER_NAME=receipts
```

## Deployment Best Practices

1. **Always test locally first** with the same Python version (3.12)
2. **Use explicit version pinning** for critical dependencies
3. **Monitor startup logs** in Azure Portal > Log Stream
4. **Set up Application Insights** for better monitoring
5. **Use staging slots** for testing deployments

## Startup.sh Features

The startup script now includes:
- ✅ Virtual environment corruption detection and recovery
- ✅ Dependency conflict resolution (websockets, psycopg2)
- ✅ Comprehensive dependency verification
- ✅ Graceful migration error handling
- ✅ Environment-based worker configuration
- ✅ Hash-based dependency update optimization
- ✅ Critical package verification before startup

## Logs to Monitor

Watch these log entries to identify issues:

- `"Creating virtual environment..."` - New venv creation
- `"Virtual environment appears corrupted..."` - Corruption detected
- `"psycopg2 not found, attempting to install..."` - Database driver issues
- `"WARNING: Database migrations failed..."` - Migration problems
- `"All critical dependencies verified successfully!"` - Successful dependency check