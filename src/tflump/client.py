"""An httpx Client configured for TfL."""

from __future__ import annotations

import random
import time
from collections import deque
from datetime import datetime, timezone

import httpx

try:
    from importlib.metadata import version
except ImportError:
    from importlib_metadata import version


__version__ = version("tflump")


class RateLimit(httpx.BaseTransport):
    """Implement naive rate limiting in composed Transport."""

    ## backoff
    FACTOR: float = 0.5
    BASE: float = 2

    ## rate limiting
    MAX_REQUESTS: int
    REQUEST_PERIOD: int
    __history: deque[datetime]

    ## debounce
    __prev: datetime
    __debounce: float

    def __init__(
        self,
        transport: httpx.BaseTransport,
        max_requests: int = 500,
        request_period: int = 60,
    ):
        self.transport = transport

        self.MAX_REQUESTS = max_requests
        self.REQUEST_PERIOD = request_period
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

        while len(self.__history) >= self.MAX_REQUESTS:
            # Slide history window
            while len(self.__history) > 0 and delta() > self.REQUEST_PERIOD:
                self.__history.popleft()

            # Throttle if history still exceeds max
            if len(self.__history) >= self.MAX_REQUESTS:
                elapsed = (now - timestamp).total_seconds()
                remaining = self.REQUEST_PERIOD - elapsed
                # Backoff
                if remaining > 0:
                    backoff = (
                        (self.FACTOR * self.BASE**backoff_count) + random.uniform(0, 1)  # noqa: S311
                    )
                    backoff_count += 1
                    time.sleep(min(remaining, backoff))

                now = datetime.now(timezone.utc)

        response = self.transport.handle_request(request)

        self.__history.append(now)

        return response


def get_tfl_client(
    app_id: str = "",
    app_key: str = "",
    retries: int = 3,
    max_requests: int = 500,
    request_period: int = 60,
) -> httpx.Client:
    """Create client configured for TfL."""
    headers = {
        "user-agent": f"python-lump/{__version__,}",
        "app_id": app_id,
        "app_key": app_key,
    }

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
