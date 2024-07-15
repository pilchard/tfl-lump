"""An httpx Client configured for TfL."""

from __future__ import annotations

import random
import time
from collections import deque
from datetime import datetime, timezone

import httpx

from .config import get_settings

try:
    from importlib.metadata import version
except ImportError:
    from importlib_metadata import version

__version__ = version("tflump")

settings = get_settings()


class RateLimit(httpx.BaseTransport):
    """Implement naive rate limiting in composed Transport."""

    ## backoff
    factor: float = 0.5
    base: float = 2

    ## rate limiting
    max_requests: int
    request_period: int
    __history: deque[datetime]

    ## debounce
    __prev: datetime
    __debounce: float

    def __init__(
        self,
        transport: httpx.BaseTransport,
        max_requests: int,
        request_period: int,
    ) -> None:
        self.transport = transport

        self.max_requests = max_requests
        self.request_period = request_period
        self.__history = deque()

        self.__prev = datetime.now(timezone.utc)
        self.__debounce = (request_period / max_requests) * 0.7

        # Initial configuration

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        """Implement naive rate limiting in composed Transport."""
        timestamp = now = datetime.now(timezone.utc)
        backoff_count: int = 0

        # Debounce
        pause = (now - self.__prev).total_seconds()
        if pause < self.__debounce:
            time.sleep(self.__debounce - pause)

        self.__prev = timestamp = now = datetime.now(timezone.utc)

        def delta() -> float:
            """Calculate max request delta."""
            try:
                return (now - self.__history[0]).total_seconds()
            except IndexError:
                return 0

        while len(self.__history) >= self.max_requests:
            # Slide history window
            while len(self.__history) > 0 and delta() > self.request_period:
                self.__history.popleft()

            # Throttle if history still exceeds max
            if len(self.__history) >= self.max_requests:
                elapsed = (now - timestamp).total_seconds()
                remaining = self.request_period - elapsed
                # Backoff
                if remaining > 0:
                    backoff = (
                        (self.factor * self.base**backoff_count) + random.uniform(0, 1)  # noqa: S311
                    )
                    backoff_count += 1
                    time.sleep(min(remaining, backoff))

                now = datetime.now(timezone.utc)

        response = self.transport.handle_request(request)

        self.__history.append(now)

        return response


def get_tfl_client() -> httpx.Client:
    """Create client configured for TfL."""
    headers = {
        "user-agent": f"python-lump/{__version__}",
    }
    max_requests = 50
    request_period = 60
    retries = 3

    app_id = settings.tfl.app_id
    app_key = settings.tfl.app_key

    if app_id is not None:
        headers["app_id"] = app_id

    if app_key is not None:
        headers["app_key"] = app_key.get_secret_value()
        max_requests = 500

    transport = RateLimit(
        httpx.HTTPTransport(retries=retries),
        max_requests=max_requests,
        request_period=request_period,
    )

    return httpx.Client(
        headers=headers,
        base_url="https://api.tfl.gov.uk",
        transport=transport,
        timeout=10.0,
    )


## Usage
# with get_tfl_client(app_id="app_id", app_key="app_key") as client:
#     pass
