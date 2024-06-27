"""LexyClient exception classes."""

from typing import Optional

import httpx


class LexyClientError(Exception):
    """Base exception class for LexyClient errors."""

    def __init__(
        self,
        message: str,
        response_data: Optional[dict] = None,
        response: Optional[httpx.Response] = None,
    ):
        super().__init__(message)
        self.message = message
        self.response_data = response_data
        self.response = response

    def __str__(self):
        return f"{self.message}"


class LexyAPIError(LexyClientError):
    """Exception class for API errors."""

    def __init__(
        self, message: str = "Lexy API error", response: Optional[httpx.Response] = None
    ):
        if response:
            response_data = {
                "status_code": response.status_code,
                "text": response.text,
                "url": response.url,
            }
            message = (
                f"{message} "
                f"'{response.status_code} {response.reason_phrase}' "
                f"for url '{response.url}'\n"
                f"\t{response.text}"
            )
        else:
            response_data = None
        super().__init__(message, response_data, response)


class NotFoundError(LexyAPIError):
    """Exception class for 404 errors."""

    def __init__(
        self, message: str = "Lexy API error", response: Optional[httpx.Response] = None
    ):
        super().__init__(message, response)


def handle_response(response: httpx.Response) -> None:
    """Handle API response."""
    if response.status_code == 404:
        raise NotFoundError(response=response)
    elif response.status_code >= 400:
        raise LexyAPIError(response=response)
