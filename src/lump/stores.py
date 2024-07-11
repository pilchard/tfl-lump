"""TfL Model Stores."""

from __future__ import annotations

import csv
import importlib
import pickle

import httpx
from pydantic import ValidationError

from lump.client import get_tfl_client
from lump.config import get_settings
from lump.models.line import Line
from lump.models.route import RouteSequence
from lump.models.shared import Direction, ModeName
from lump.models.stoppoint import StopPoint

SETTINGS = get_settings()


class StopPointStore:
    """A store of StopPoint instances keyed by NaPTAN ID."""

    def __init__(self) -> None:
        self.storepath = importlib.resources.files("lump") / "data/stoppoints.pkl"

        if self.storepath.is_file():
            with self.storepath.open("rb") as datafile:
                self.data = pickle.load(datafile)
        else:
            self.data = {}

    def has_stop_point(self, naptan_id: str) -> bool:
        """Check if store includes NaPTAN ID."""
        return naptan_id in self.data

    def get_stop_point(self, naptan_id: str) -> dict[str, StopPoint]:
        """Return StopPoint for passed NaPTAN ID if it exists, otherwise None."""
        return self.data.get(naptan_id, None)

    def add_stop_points(self, stoppoints: list[StopPoint]) -> None:
        """Add StopPoints to the store."""
        dirty = False
        for stoppoint in stoppoints:
            if stoppoint.id not in self.data:
                self.data[stoppoint.id] = stoppoint
                dirty = True

        if dirty:
            self.save()

    def save(self) -> None:
        """Save the RouteStore object to the location specified in `self.datafile`."""
        with self.storepath.open("wb") as lib_file:
            pickle.dump(self.data, lib_file)
            lib_file.close()

    def write_csv(self) -> None:
        """Write store data to csv file."""
        csv_path = importlib.resources.files("lump") / "data/stoppoints.csv"

        with csv_path.open("w", newline="") as csv_file:
            fieldnames = list(StopPoint.__fields__.keys())
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

            writer.writeheader()
            for stop_point in self.data.values():
                writer.writerow(stop_point.model_dump())


class LineStore:
    """A store of StopPoint instances keyed by NaPTAN ID."""

    def __init__(
        self,
        client: httpx.Client,
        mode: ModeName,
        stop_point_store: StopPointStore | None = None,
    ) -> None:
        self.client = client
        self.storepath = importlib.resources.files("lump") / f"data/lines-{mode}.pkl"
        self.endpoint = "/Line/Mode/bus/Route?serviceTypes=Regular,Night"

        if stop_point_store is None:
            self.stop_point_store = StopPointStore()
        else:
            self.stop_point_store = stop_point_store

        self.data = {}

    def load(self) -> None:
        """Load the store data from file if exists otherwise query TfL."""
        if self.storepath.is_file():
            with self.storepath.open("rb") as datafile:
                self.data = pickle.load(datafile)
        else:
            # Fetch from API

            line_list = self.request(self.endpoint).json()

            for line_dict in line_list[0:3]:
                if line_dict["id"] not in self.data:
                    ## get sequence for each direction
                    for section in line_dict["routeSections"]:
                        route_sequence = self.get_route_sequence(
                            line_dict["id"],
                            section["direction"],
                        )

                        section["isOutboundOnly"] = route_sequence.is_outbound_only
                        section["lineStrings"] = route_sequence.line_strings
                        section["orderedLineRoutes"] = (
                            route_sequence.ordered_line_routes
                        )

                    ## parse route and add to store
                    try:
                        line = Line.model_validate(line_dict)
                        self.data[line.id] = line
                    except ValidationError as exc:
                        # print(f"Validation error: {exc.errors()[0]!r}")
                        raise exc from exc

        self.save()

    def get_route_sequence(self, line_id: str, direction: Direction) -> RouteSequence:
        endpoint = f"/Line/{line_id}/Route/Sequence/{direction}"

        seq_dict = self.request(endpoint).json()

        try:
            # Add StopPoints to store
            for seq in seq_dict["stopPointSequences"]:
                stop_points = []
                for stop_point in seq["stopPoint"]:
                    stop_points.append(StopPoint.model_validate(stop_point))

                self.stop_point_store.add_stop_points(stop_points)

        except ValidationError as exc:
            # print("\nFailed to parse stop point in sequence:")
            # print(f"Validation error: {exc.errors()[0]!r}")
            raise exc from exc

        try:
            return RouteSequence.model_validate(seq_dict)

        except ValidationError as exc:
            # print(f"Validation error: {exc.errors()[0]!r}")
            raise exc from exc

    def request(self, endpoint: str) -> httpx.Response:
        """Query endpoint."""
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

    def save(self) -> None:
        """Save the RouteStore object to the location specified in `self.datafile`."""
        with self.storepath.open("wb") as lib_file:
            pickle.dump(self.data, lib_file)
            lib_file.close()


if __name__ == "__main__":
    ## StopPointStore
    # sp_store = StopPointStore()
    # sp_stub = """{"$type":"Tfl.Api.Presentation.Entities.MatchedStop,Tfl.Api.Presentation.Entities","parentId":"490G00010877","stationId":"490G00010877","icsId":"1010877","topMostParentId":"490G00010877","modes":["bus"],"stopType":"NaptanPublicBusCoachTram","stopLetter":"H","lines":[{"$type":"Tfl.Api.Presentation.Entities.Identifier,Tfl.Api.Presentation.Entities","id":"177","name":"177","uri":"/Line/177","type":"Line","crowding":{"$type":"Tfl.Api.Presentation.Entities.Crowding,Tfl.Api.Presentation.Entities"},"routeType":"Unknown","status":"Unknown"},{"$type":"Tfl.Api.Presentation.Entities.Identifier,Tfl.Api.Presentation.Entities","id":"381","name":"381","uri":"/Line/381","type":"Line","crowding":{"$type":"Tfl.Api.Presentation.Entities.Crowding,Tfl.Api.Presentation.Entities"},"routeType":"Unknown","status":"Unknown"},{"$type":"Tfl.Api.Presentation.Entities.Identifier,Tfl.Api.Presentation.Entities","id":"n381","name":"N381","uri":"/Line/n381","type":"Line","crowding":{"$type":"Tfl.Api.Presentation.Entities.Crowding,Tfl.Api.Presentation.Entities"},"routeType":"Unknown","status":"Unknown"},{"$type":"Tfl.Api.Presentation.Entities.Identifier,Tfl.Api.Presentation.Entities","id":"p12","name":"P12","uri":"/Line/p12","type":"Line","crowding":{"$type":"Tfl.Api.Presentation.Entities.Crowding,Tfl.Api.Presentation.Entities"},"routeType":"Unknown","status":"Unknown"},{"$type":"Tfl.Api.Presentation.Entities.Identifier,Tfl.Api.Presentation.Entities","id":"p13","name":"P13","uri":"/Line/p13","type":"Line","crowding":{"$type":"Tfl.Api.Presentation.Entities.Crowding,Tfl.Api.Presentation.Entities"},"routeType":"Unknown","status":"Unknown"}],"status":true,"id":"490010877H","name":"PeckhamBusStation","lat":51.473372,"lon":-0.067963}"""

    # sp_store.add_stop_points([StopPoint.model_validate_json(sp_stub)])
    # s1 = sp_store.get_stop_point("490010877H")
    # print(s1)

    # sp_store2 = StopPointStore()
    # s2 = sp_store2.get_stop_point("490010877H")
    # print(s2)

    # sp_store2 = sp_store = None

    ## LineStore
    # Usage
    with get_tfl_client(
        app_id=SETTINGS.tfl.app_id,
        app_key=SETTINGS.tfl.app_key.get_secret_value(),
        max_requests=500,
        request_period=60,
    ) as client:
        sp_store = StopPointStore()
        l_store = LineStore(client=client, mode=ModeName.BUS, stop_point_store=sp_store)

        # print(sp_store.data.items())

        l_store.load()

        print(len(sp_store.data))
        sp_store.write_csv()
