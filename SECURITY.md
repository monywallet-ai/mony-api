# API Documentation Security

This document describes the authentication system for API documentation endpoints.

## Overview

The API includes HTTP Basic Authentication for documentation endpoints (`/docs`, `/redoc`, `/openapi.json`) to protect sensitive API information in production environments.

## Configuration

### Environment Variables

Configure these variables in your Terraform or environment configuration:

```bash
# Documentation Authentication (Required for production)
ENABLE_DOCS_AUTH=true                    # Enable/disable docs authentication
DOCS_USERNAME=your-docs-username         # Username for docs access
DOCS_PASSWORD=your-secure-docs-password  # Strong password for docs access
```

### Auto-Detection

- **Local Environment**: Authentication is disabled by default (`ENABLE_DOCS_AUTH=false`)
- **Development Environment**: Authentication is disabled by default
- **Production Environment**: Authentication is **automatically enabled** (`ENABLE_DOCS_AUTH=true`)

You can override this behavior by explicitly setting `ENABLE_DOCS_AUTH`.

## Accessing Documentation

### Without Authentication (Local/Dev)
- Swagger UI: `http://your-domain/docs`
- ReDoc: `http://your-domain/redoc`
- OpenAPI JSON: `http://your-domain/openapi.json`

### With Authentication (Production)
1. Navigate to `http://your-domain/docs`
2. Enter your configured username and password
3. Access is granted for the browser session

### Information Endpoints
- Health Check: `GET /health` - Includes docs authentication status
- Docs Info: `GET /docs-info` - Public endpoint with authentication information

## Security Best Practices

### For Terraform Configuration

```hcl
# Example Terraform configuration
resource "azurerm_linux_web_app" "mony_api" {
  # ... other configuration

  app_settings = {
    ENVIRONMENT        = "production"
    ENABLE_DOCS_AUTH  = "true"
    DOCS_USERNAME     = var.docs_username      # Use Terraform variables
    DOCS_PASSWORD     = var.docs_password      # Store in secure variable
    # ... other settings
  }
}

# Secure variable definitions
variable "docs_username" {
  description = "Username for API documentation access"
  type        = string
  sensitive   = false
}

variable "docs_password" {
  description = "Password for API documentation access"
  type        = string
  sensitive   = true
}
```

### Password Security
- Use strong, unique passwords (minimum 16 characters)
- Include uppercase, lowercase, numbers, and special characters
- Store credentials securely in your infrastructure-as-code
- Rotate credentials regularly
- Never commit credentials to version control

### Monitoring
- Monitor `/docs-info` endpoint for authentication status
- Check `/health` endpoint for system status including docs configuration
- Implement logging for failed authentication attempts (future enhancement)

## Implementation Details

### Authentication Flow
1. Client accesses documentation URL
2. If authentication is enabled, HTTP 401 is returned with `WWW-Authenticate: Basic` header
3. Browser prompts for credentials
4. Credentials are validated using secure comparison (`secrets.compare_digest`)
5. Access is granted for the session

### Technical Features
- **Secure Comparison**: Uses `secrets.compare_digest()` to prevent timing attacks
- **Conditional Loading**: Authentication only loads when enabled
- **Environment Aware**: Automatically adjusts based on deployment environment
- **Multiple Endpoints**: Protects Swagger UI, ReDoc, and OpenAPI JSON
- **Session Based**: No need to re-authenticate during browser session

### Error Handling
- **401 Unauthorized**: Incorrect credentials
- **Secure Headers**: Proper `WWW-Authenticate` header for HTTP Basic Auth
- **User Friendly**: Clear error messages without revealing implementation details

## Troubleshooting

### Common Issues

1. **Can't access docs in production**
   - Check `ENABLE_DOCS_AUTH` environment variable
   - Verify `DOCS_USERNAME` and `DOCS_PASSWORD` are set
   - Check `/docs-info` endpoint for current status

2. **Authentication not working**
   - Ensure credentials match exactly (case-sensitive)
   - Verify environment variables are properly set
   - Check `/health` endpoint for configuration status

3. **Terraform deployment issues**
   - Verify sensitive variables are properly defined
   - Check Azure Web App configuration in Azure Portal
   - Ensure variables are applied after deployment

### Debug Commands

```bash
# Check current configuration
curl https://your-domain/docs-info

# Check health status
curl https://your-domain/health

# Test authentication
curl -u username:password https://your-domain/docs
```

## Future Enhancements

- Rate limiting for authentication attempts
- Audit logging for documentation access
- JWT-based authentication option
- Role-based access control
- Integration with Azure AD or other identity providers