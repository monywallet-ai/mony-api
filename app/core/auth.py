"""
Authentication utilities for API documentation
"""
import secrets
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from .settings import settings

security = HTTPBasic()


def authenticate_docs(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)]
):
    """
    Authenticate users for API documentation access.
    Uses HTTP Basic Authentication with configurable credentials.
    """
    
    # If docs authentication is disabled, allow access
    if not settings.ENABLE_DOCS_AUTH:
        return True
    
    current_username_bytes = credentials.username.encode("utf8")
    correct_username_bytes = settings.DOCS_USERNAME.encode("utf8")
    is_correct_username = secrets.compare_digest(
        current_username_bytes, correct_username_bytes
    )
    
    current_password_bytes = credentials.password.encode("utf8")
    correct_password_bytes = settings.DOCS_PASSWORD.encode("utf8")
    is_correct_password = secrets.compare_digest(
        current_password_bytes, correct_password_bytes
    )
    
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect documentation credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    return True


def get_docs_auth_dependency():
    """
    Get the authentication dependency for docs.
    Returns None if authentication is disabled.
    """
    return authenticate_docs if settings.ENABLE_DOCS_AUTH else None