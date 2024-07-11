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
    history: deque[datetime]

    ## debounce
    _prev: datetime
    _debounce: float

    def __init__(
        self,
        transport: httpx.BaseTransport,
        max_requests: int = 500,
        request_period: int = 60,
    ):
        self.transport = transport

        self.MAX_REQUESTS = max_requests
        self.REQUEST_PERIOD = request_period
        self.history = deque()

        self._prev = datetime.now(timezone.utc)
        self._debounce = (request_period / max_requests) * 0.7

        # Initial configuration

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        """Implement naive rate limiting in composed Transport."""
        timestamp = now = datetime.now(timezone.utc)
        backoff_count: int = 0

        # Debounce
        if (now - self._prev).total_seconds() < self._debounce:
            time.sleep(self._debounce - (now - self._prev).total_seconds())

        self._prev = timestamp = now = datetime.now(timezone.utc)

        def delta() -> float:
            """Calculate max request delta."""
            try:
                return (now - self.history[0]).total_seconds()
            except IndexError:
                return 0

        while len(self.history) >= self.MAX_REQUESTS:
            # Slide history window
            while len(self.history) > 0 and delta() > self.REQUEST_PERIOD:
                self.history.popleft()

            # Throttle if history still exceeds max
            if len(self.history) >= self.MAX_REQUESTS:
                elapsed = (now - timestamp).total_seconds()
                if elapsed < self.REQUEST_PERIOD:
                    # Backoff
                    backoff = (
                        (self.FACTOR * self.BASE**backoff_count) + random.uniform(0, 1)  # noqa: S311
                    )
                    backoff_count += 1
                    wait = min((self.REQUEST_PERIOD - elapsed), backoff)
                    print(f"Waiting: {wait} seconds")
                    time.sleep(wait)

                now = datetime.now(timezone.utc)

        response = self.transport.handle_request(request)

        self.history.append(now)

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
# with get_tfl_client(
#     app_id="app_id",
#     app_key="app_key",
#     max_requests=500,
#     request_period=60,
# ) as client:


if __name__ == "__main__":
    from tflump.config import get_settings

    settings = get_settings()

    t1 = datetime.now(timezone.utc)
    with get_tfl_client(
        app_id=settings.tfl.app_id,
        app_key=settings.tfl.app_key.get_secret_value(),
        max_requests=500,
        request_period=60,
    ) as client:
        try:
            lines = client.get("/Line/Mode/bus")
            lines.raise_for_status()
        except httpx.RequestError as exc:
            print(f"An error occurred while requesting {exc.request.url!r}.")
        except httpx.HTTPStatusError as exc:
            print(
                f"Error response {exc.response.status_code} while requesting {exc.request.url!r}.",
            )

        try:
            for n, line in enumerate(lines.json()[0:10]):
                r = client.get(f"/Line/{line["id"]}/Route?serviceTypes=Regular")

                r.raise_for_status()
                print(
                    f"{line["id"]} {r} - {n} - {(datetime.now(timezone.utc) - t1).total_seconds()}",
                )
        except httpx.RequestError as exc:
            print(f"An error occurred while requesting {exc.request.url!r}.")
        except httpx.HTTPStatusError as exc:
            print(
                f"Error response {exc.response.status_code} while requesting {exc.request.url!r}.",
            )
    t2 = datetime.now(timezone.utc)
