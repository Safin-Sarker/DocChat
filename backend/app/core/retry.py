"""Async and sync retry utilities with exponential backoff."""

import asyncio
import errno
import logging
import time as _time

logger = logging.getLogger(__name__)


def is_retryable(exc: BaseException) -> bool:
    """Determine whether an exception is transient and worth retrying.

    Returns True for network/timeout/server errors.
    Returns False for auth, permission, or validation errors.
    """
    # stdlib network errors — always retryable
    if isinstance(exc, (ConnectionError, TimeoutError)):
        return True

    # OSError subtypes — only retry network-related errnos
    if isinstance(exc, OSError) and not isinstance(exc, (ConnectionError, TimeoutError)):
        retryable_errnos = {
            errno.ECONNREFUSED, errno.ECONNRESET, errno.ECONNABORTED,
            errno.ETIMEDOUT, errno.ENETUNREACH, errno.EHOSTUNREACH,
        }
        return getattr(exc, "errno", None) in retryable_errnos

    # Neo4j transient errors
    try:
        from neo4j.exceptions import ServiceUnavailable, TransientError
        if isinstance(exc, (ServiceUnavailable, TransientError)):
            return True
    except ImportError:
        pass

    # botocore connection/timeout errors
    try:
        from botocore.exceptions import (
            EndpointConnectionError,
            ConnectTimeoutError,
            ReadTimeoutError,
        )
        if isinstance(exc, (EndpointConnectionError, ConnectTimeoutError, ReadTimeoutError)):
            return True
    except ImportError:
        pass

    # botocore ClientError — only retry 5xx and throttling
    try:
        from botocore.exceptions import ClientError
        if isinstance(exc, ClientError):
            http_status = exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode", 0)
            code = exc.response.get("Error", {}).get("Code", "")
            if http_status >= 500 or code in (
                "Throttling", "TooManyRequestsException", "RequestLimitExceeded",
            ):
                return True
            return False
    except ImportError:
        pass

    # Pinecone errors — retry server errors, not auth/validation
    try:
        from pinecone.exceptions import PineconeException
        if isinstance(exc, PineconeException):
            msg = str(exc).lower()
            if "unauthorized" in msg or "forbidden" in msg or "invalid" in msg:
                return False
            return True
    except ImportError:
        pass

    return False


async def retry_async(
    func,
    *args,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
    operation_name: str = "operation",
    **kwargs,
):
    """Execute an async callable with retry and exponential backoff.

    Args:
        func: Async callable to execute.
        max_attempts: Maximum number of attempts (including the first).
        base_delay: Initial delay in seconds between retries.
        max_delay: Maximum delay cap in seconds.
        operation_name: Human-readable name for logging.

    Returns:
        The return value of func.

    Raises:
        The last exception if all attempts fail or the error is not retryable.
    """
    last_exception = None
    for attempt in range(1, max_attempts + 1):
        try:
            return await func(*args, **kwargs)
        except Exception as exc:
            last_exception = exc
            if attempt == max_attempts or not is_retryable(exc):
                logger.warning(
                    "%s failed (attempt %d/%d, not retrying): %s",
                    operation_name, attempt, max_attempts, exc,
                )
                raise
            delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
            logger.warning(
                "%s failed (attempt %d/%d, retrying in %.1fs): %s",
                operation_name, attempt, max_attempts, delay, exc,
            )
            await asyncio.sleep(delay)

    raise last_exception  # unreachable, satisfies type checker


def retry_sync(
    func,
    *args,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
    operation_name: str = "operation",
    **kwargs,
):
    """Execute a sync callable with retry and exponential backoff.

    Same semantics as retry_async but for synchronous functions.
    """
    last_exception = None
    for attempt in range(1, max_attempts + 1):
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            last_exception = exc
            if attempt == max_attempts or not is_retryable(exc):
                logger.warning(
                    "%s failed (attempt %d/%d, not retrying): %s",
                    operation_name, attempt, max_attempts, exc,
                )
                raise
            delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
            logger.warning(
                "%s failed (attempt %d/%d, retrying in %.1fs): %s",
                operation_name, attempt, max_attempts, delay, exc,
            )
            _time.sleep(delay)

    raise last_exception
