# src/alerts/exceptions.py
from fastapi import HTTPException, status


class AlertException(HTTPException):
    """Base exception for alert-related errors"""
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)


class AlertNotFoundException(AlertException):
    """Raised when alert is not found"""
    def __init__(self, alert_id: int):
        super().__init__(
            detail=f"Alert with id {alert_id} not found",
            status_code=status.HTTP_404_NOT_FOUND
        )


class AlertLimitExceededException(AlertException):
    """Raised when user exceeds alert limit"""
    def __init__(self, limit: int):
        super().__init__(
            detail=f"Maximum number of alerts ({limit}) exceeded",
            status_code=status.HTTP_400_BAD_REQUEST
        )


class InvalidAlertException(AlertException):
    """Raised when alert data is invalid"""
    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=status.HTTP_400_BAD_REQUEST)


class UnauthorizedAlertAccessException(AlertException):
    """Raised when user tries to access another user's alert"""
    def __init__(self):
        super().__init__(
            detail="You don't have permission to access this alert",
            status_code=status.HTTP_403_FORBIDDEN
        )