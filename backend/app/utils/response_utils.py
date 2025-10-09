from typing import Any, List, Optional
from fastapi import status
from fastapi.responses import JSONResponse
from backend.app.schemas import schemas


def success_response(
        data: Any = None,
        message: str = "Success",
        status_code: int = status.HTTP_200_OK
) -> JSONResponse:
    """Standard success response"""
    response_data = {
        "success": True,
        "message": message,
        "data": data
    }
    return JSONResponse(status_code=status_code, content=response_data)


def error_response(
        message: str = "Error",
        error_code: str = None,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Any = None
) -> JSONResponse:
    """Standard error response"""
    response_data = {
        "success": False,
        "message": message,
        "error_code": error_code
    }
    if details:
        response_data["details"] = details

    return JSONResponse(status_code=status_code, content=response_data)


def paginated_response(
        data: List[Any],
        total: int,
        page: int,
        page_size: int
) -> JSONResponse:
    """Paginated data response"""
    total_pages = (total + page_size - 1) // page_size
    pagination_data = {
        "data": data,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1
    }
    return success_response(data=pagination_data)


def created_response(data: Any = None, message: str = "Resource created successfully"):
    """201 Created response"""
    return success_response(data=data, message=message, status_code=status.HTTP_201_CREATED)


def deleted_response(message: str = "Resource deleted successfully"):
    """204 No Content response for deletions"""
    return JSONResponse(
        status_code=status.HTTP_204_NO_CONTENT,
        content=None
    )


def not_found_response(message: str = "Resource not found"):
    """404 Not Found response"""
    return error_response(
        message=message,
        error_code="NOT_FOUND",
        status_code=status.HTTP_404_NOT_FOUND
    )


def validation_error_response(message: str = "Validation error", details: Any = None):
    """422 Validation Error response"""
    return error_response(
        message=message,
        error_code="VALIDATION_ERROR",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details=details
    )