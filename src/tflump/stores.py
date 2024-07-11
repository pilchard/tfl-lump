"""TfL Model Stores."""

from __future__ import annotations

import importlib
import json
import pickle
from pathlib import Path

import httpx
from pydantic import ValidationError

from .models.line import Line
from .models.route import RouteSequence
from .models.shared import Direction, ModeName
from .models.stoppoint import StopPoint, StopPointList


class Store:
    """Base Store class."""

    def __init__(self, storename: str) -> None:
        self.datadir = importlib.resources.files("tflump")
        self.storename = storename
        self.data = {}

    def load(self) -> None:
        """Load the store data from file if exists otherwise query TfL."""
        datafile = self.datadir / (self.storename + ".pkl")

        if datafile.is_file():
            with datafile.open("rb") as datafile:
                self.data = pickle.load(datafile)
        else:
            self.data = self.fetch()
            self.save()

    def fetch(self) -> dict:
        """Fetch store data."""
        return {}

    def save(self, filename: str | None = None) -> None:
        """Save the store data object using pickle."""
        if filename is None:
            filepath = self.datadir / (self.storename + ".pkl")
        else:
            filepath = self.datadir / (filename + ".pkl")

        with filepath.open("wb") as lib_file:
            pickle.dump(self.data, lib_file)
            lib_file.close()

    def write_json(self, filepath: str | None = None) -> json:
        """Write the store data to a JSON file."""
        if filepath is None:
            filepath = self.datadir / (self.storename + ".json")
            with filepath.open("w") as json_file:
                data_values = list(self.data.values())
                json.dump(data_values, json_file, indent=4, default=str)
        else:
            with Path(filepath).open("w") as json_file:
                data_values = list(self.data.values())
                json.dump(data_values, json_file, indent=4, default=str)


class StopPointStore(Store):
    """A store of StopPoint instances keyed by NaPTAN ID."""

    def __init__(self) -> None:
        super().__init__("data/stoppoints")

    def has_stop_point(self, naptan_id: str) -> bool:
        """Check if store includes NaPTAN ID."""
        return naptan_id in self.data

    def get_stop_point(self, naptan_id: str) -> StopPoint:
        """Return StopPoint for passed NaPTAN ID if it exists, otherwise None."""
        return self.data.get(naptan_id, None)

    def get_stop_points(self, naptan_ids: list[str]) -> list[StopPoint]:
        """Return a list of StopPoints for passed NaPTAN IDs, missing ids will be replaced with None."""
        return [self.data.get(naptan_id, None) for naptan_id in naptan_ids]

    def add_stop_points(self, stoppoints: list[StopPoint]) -> None:
        """Add StopPoints to the store."""
        dirty = False
        for stoppoint in stoppoints:
            if stoppoint["id"] not in self.data:
                self.data[stoppoint["id"]] = stoppoint
                dirty = True

        if dirty:
            self.save()


class LineStore(Store):
    """A store of StopPoint instances keyed by NaPTAN ID."""

    def __init__(
        self,
        client: httpx.Client,
        mode: ModeName,
        stop_point_store: StopPointStore | None = None,
    ) -> None:
        super().__init__(f"data/lines-{mode}")
        self.client = client
        self.mode = mode

        if stop_point_store is None:
            self.stop_point_store = StopPointStore()
        else:
            self.stop_point_store = stop_point_store

        self.stop_point_store.load()

    def fetch(self) -> dict:
        """Fetch Line and Route data from TfL."""
        temppath = self.datadir / (self.storename + "_temp.pkl")

        if temppath.is_file():
            with temppath.open("rb") as datafile:
                temp = pickle.load(datafile)
        else:
            temp = {}

        try:
            line_list = self.request(
                f"/Line/Mode/{self.mode}/Route?serviceTypes=Regular,Night",
            ).json()

            for line_dict in line_list:
                if line_dict["id"] not in temp:
                    ## get sequence for each direction
                    for section in line_dict["routeSections"]:
                        seq_dict = self.request(
                            f"/Line/{line_dict["id"]}/Route/Sequence/{section["direction"]}",
                        ).json()

                        # Add StopPoints to store
                        for seq in seq_dict["stopPointSequences"]:
                            stop_points = StopPointList.model_validate(seq["stopPoint"])
                            self.stop_point_store.add_stop_points(
                                stop_points.model_dump(),
                            )

                        # merge sequence attributes into `route_section`
                        route_sequence = RouteSequence.model_validate(seq_dict)

                        section["isOutboundOnly"] = route_sequence.is_outbound_only
                        section["lineStrings"] = route_sequence.line_strings
                        section["orderedLineRoutes"] = (
                            route_sequence.ordered_line_routes
                        )

                    # Parse line and index in temp
                    line = Line.model_validate(line_dict)
                    temp[line.id] = line.model_dump()

        except Exception:
            with temppath.open("wb") as lib_file:
                pickle.dump(temp, lib_file)
                lib_file.close()
            return {}
        else:
            # cleanup temp file
            temppath.unlink(missing_ok=True)

            return temp

    def _get_route_sequence(self, line_id: str, direction: Direction) -> RouteSequence:
        """Fetch route sequence for given Line ID and Direction.

        Saves sequence StopPoint data to the owned StopPointStore.
        """
        endpoint = f"/Line/{line_id}/Route/Sequence/{direction}"

        seq_dict = self.request(endpoint).json()

        try:
            # Add StopPoints to store
            for seq in seq_dict["stopPointSequences"]:
                stop_points = [
                    StopPoint.model_validate(stop_point)
                    for stop_point in seq["stopPoint"]
                ]

                self.stop_point_store.add_stop_points(stop_points)

        except ValidationError as exc:
            # print(repr(exc.errors()[0]))
            raise exc from exc

        try:
            return RouteSequence.model_validate(seq_dict)

        except ValidationError as exc:
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
