# """Client tests (rough)."""

# from datetime import datetime, timezone

# import httpx

# from tflump import (
#     get_settings,
#     get_tfl_client,
# )

# settings = get_settings()

# with get_tfl_client() as client:
#     try:
#         lines = client.get("/Line/Mode/bus")
#         lines.raise_for_status()
#     except httpx.RequestError as exc:
#         print(f"An error occurred while requesting {exc.request.url!r}.")
#     except httpx.HTTPStatusError as exc:
#         print(
#             f"Error response {exc.response.status_code} while requesting {exc.request.url!r}.",
#         )

#     try:
#         for n, line in enumerate(lines.json()[0:10]):
#             r = client.get(f"/Line/{line["id"]}/Route?serviceTypes=Regular")

#             r.raise_for_status()
#             print(
#                 f"{line["id"]} {r} - {n} - {(datetime.now(timezone.utc) - t1).total_seconds()}",
#             )
#     except httpx.RequestError as exc:
#         print(f"An error occurred while requesting {exc.request.url!r}.")
#     except httpx.HTTPStatusError as exc:
#         print(
#             f"Error response {exc.response.status_code} while requesting {exc.request.url!r}.",
#         )
