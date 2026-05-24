import logging
from typing import Any

logger = logging.getLogger("ai_project_manager")


class ServiceError(Exception):
    def __init__(
        self,
        error_type: str,
        service: str,
        message: str,
        details: Any = None,
    ):
        self.error_type = error_type
        self.service = service
        self.message = message
        self.details = details
        super().__init__(message)

    def to_dict(self) -> dict:
        return error_response(
            error_type=self.error_type,
            service=self.service,
            message=self.message,
            details=self.details,
        )


def error_response(
    error_type: str,
    service: str,
    message: str,
    details: Any = None,
) -> dict:
    return {
        "success": False,
        "error": {
            "type": error_type,
            "service": service,
            "message": message,
            "details": details,
        },
    }


def is_error_response(value: Any) -> bool:
    return isinstance(value, dict) and value.get("success") is False and "error" in value


def error_message(value: Any, fallback: str = "The requested operation failed.") -> str:
    if is_error_response(value):
        error = value.get("error") or {}
        message = error.get("message")
        if isinstance(message, str) and message:
            return message
    if isinstance(value, dict) and isinstance(value.get("error"), str):
        return value["error"]
    return fallback
