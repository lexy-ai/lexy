from datetime import datetime, timedelta, timezone
from typing import Literal
from urllib.parse import parse_qs, urlparse


def presigned_url_is_expired(url: str, storage_service: str = "s3") -> bool:
    if storage_service == "s3":
        return signed_url_is_expired(url, svc="Amz")
    elif storage_service == "gcs":
        return signed_url_is_expired(url, svc="Goog")
    elif storage_service == "azure":
        raise NotImplementedError
    else:
        raise ValueError(
            f"Unsupported storage service: {storage_service} - "
            f"must be one of the following: s3, gcs, azure"
        )


def signed_url_is_expired(url: str, svc: Literal["Amz", "Goog"]):
    """Checks if a signed URL (V2 or V4) has expired.

    Args:
        url (str): The signed URL string.
        svc (Literal['Amz', 'Goog']): The service query parameter used to check for
            expiration in V4 signatures. Either 'Amz' for AWS or 'Goog' for GCP.

    Returns:
        True if the signed URL is expired, False otherwise.

    Raises:
        ValueError: If no expiration found in signed url.
    """
    query_params = parse_qs(urlparse(url).query)
    # V4 signature
    if f"X-{svc}-Expires" in query_params:
        expires_in = int(query_params[f"X-{svc}-Expires"][0])
        issued_at_dt = datetime.fromisoformat(query_params[f"X-{svc}-Date"][0])
        expires_at_dt = issued_at_dt + timedelta(seconds=expires_in)
        return expires_at_dt < datetime.now(tz=timezone.utc)
    # V2 signature
    elif "Expires" in query_params:
        expires_at = int(query_params["Expires"][0])
        expires_at_dt = datetime.fromtimestamp(expires_at, tz=timezone.utc)
        return expires_at_dt < datetime.now(tz=timezone.utc)
    else:
        raise ValueError("No expiration found in signed url")
