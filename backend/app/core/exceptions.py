from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class AppException(Exception):
    """Base exception for application errors"""

    def __init__(
            self,
            message: str,
            status_code: int = 500,
            error_code: str = None,
            details: Dict[str, Any] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationException(AppException):
    """Validation errors"""

    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            status_code=422,
            error_code="VALIDATION_ERROR",
            details=details
        )


class AuthenticationException(AppException):
    """Authentication errors"""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            status_code=401,
            error_code="AUTHENTICATION_ERROR"
        )


class AuthorizationException(AppException):
    """Authorization errors"""

    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            status_code=403,
            error_code="AUTHORIZATION_ERROR"
        )


class NotFoundException(AppException):
    """Resource not found"""

    def __init__(self, resource: str = "Resource"):
        super().__init__(
            message=f"{resource} not found",
            status_code=404,
            error_code="NOT_FOUND"
        )


class BusinessRuleException(AppException):
    """Business rule violations"""

    def __init__(self, message: str, error_code: str = "BUSINESS_RULE_VIOLATION"):
        super().__init__(
            message=message,
            status_code=400,
            error_code=error_code
        )


async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for all unhandled exceptions"""
    if isinstance(exc, AppException):
        # Handle known application exceptions
        response_data = {
            "detail": exc.message,
            "error_code": exc.error_code
        }
        if exc.details:
            response_data["details"] = exc.details

        logger.warning(
            f"AppException: {exc.message}",
            extra={
                "status_code": exc.status_code,
                "error_code": exc.error_code,
                "path": request.url.path
            }
        )

        return JSONResponse(
            status_code=exc.status_code,
            content=response_data
        )
    elif isinstance(exc, HTTPException):
        # Handle FastAPI HTTP exceptions
        logger.warning(
            f"HTTPException: {exc.detail}",
            extra={
                "status_code": exc.status_code,
                "path": request.url.path
            }
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )
    else:
        # Handle unexpected exceptions
        logger.error(
            f"Unhandled exception: {str(exc)}",
            extra={
                "path": request.url.path,
                "method": request.method
            },
            exc_info=True
        )

        # Don't expose internal details in production
        if hasattr(request.app, "state") and getattr(request.app.state, "environment", "development") == "production":
            detail = "Internal server error"
        else:
            detail = f"Internal server error: {str(exc)}"

        return JSONResponse(
            status_code=500,
            content={
                "detail": detail,
                "error_code": "INTERNAL_SERVER_ERROR"
            }
        )


# Utility functions for raising exceptions
def raise_validation_error(message: str, details: Dict[str, Any] = None):
    raise ValidationException(message, details)


def raise_not_found(resource: str = "Resource"):
    raise NotFoundException(resource)


def raise_business_rule(message: str, error_code: str = None):
    raise BusinessRuleException(message, error_code)