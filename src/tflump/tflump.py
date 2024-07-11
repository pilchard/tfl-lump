# from io import BytesIO
# import json
# import tempfile
# from typing import Iterable, Optional, Union
# import webbrowser

# import folium
# from folium.plugins.fast_marker_cluster import FastMarkerCluster
# from folium.plugins import Search
# import pandas as pd
# from pyproj import CRS, Transformer
# import requests


# _BASE_URL = 'https://naptan.api.dft.gov.uk'
# _API_VERSION = 'v1'


def get_lines_for_mode(mode: ModeName):
    datafile = f"data/lines-{mode}.pkl"
    endpoint = f"/Line/Mode/{mode}/Route?serviceTypes=Regular,Night"

    data = {}

    if os.path.isfile(datafile):
        with open(datafile, "rb") as libFile:
            data = pickle.load(libFile)
            libFile.close()

            print("Read routes from file.")

    response = _request.get(endpoint)

    if response.status_code != 200:
        raise APIError(response.status_code, response.reason)
    return response

    for line in lineStubs:
        if line["id"] not in data:
            try:
                res = query_tfl(
                    f"/Line/{line["id"]}/Route?serviceTypes={",".join(line["serviceTypes"])}",
                )
                res_json = res.json()
            except httpx.LocalProtocolError as exc:
                st.error(exc["message"])
            except httpx.HTTPError as exc:
                st.error(f"An error occurred while requesting {exc.request.url!r}.")

            ## get sequence for each direction
            for section in res_json["routeSections"]:
                routeSequence = get_route_sequence(
                    line["id"],
                    section["direction"],
                ).model_dump()

                section["lineStrings"] = routeSequence["lineStrings"]
                section["orderedLineRoutes"] = routeSequence["orderedLineRoutes"]

            ## parse route and add to store
            try:
                route = Line.model_validate(res_json)
                data[line["id"]] = route.model_dump()
            except ValidationError as exc:
                print(f"Validation error: {exc.errors()[0]!r}")
                raise exc

        percent_complete = min(percent_complete + increment, 1.0)

    my_bar.progress(1.0, text="Complete...")
    time.sleep(1)
    my_bar.empty()

    progress_text = "Fetching routes for lines"
    percent_complete: float = 0.0

    # save to file
    with open(datafile, "wb") as libFile:
        pickle.dump(data, libFile)
        libFile.close()

    # save json
    with open("data/routes.json", "w") as json_file:
        data_values = list(data.values())

        json.dump(data_values, json_file, ensure_ascii=False, indent=4, default=str)

    return data


def _request(self, endpoint: str) -> httpx.Response:
    """Query TfL endpoint."""
    try:
        response = self.client.get(endpoint)
        return response.raise_for_status()
    except httpx.RequestError as exc:
        print(f"An error occurred while requesting {exc.request.url!r}.")
        raise exc from exc
    except httpx.HTTPStatusError as exc:
        print(
            f"Error response {exc.response.status_code} while requesting {exc.request.url!r}.",
        )
        raise exc from exc
