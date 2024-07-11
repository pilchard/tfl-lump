"""TfL Model Stores."""

from __future__ import annotations

import importlib
import json
import pickle

import httpx
from pydantic import ValidationError

from .models.line import Line
from .models.route import RouteSequence
from .models.shared import Direction, ModeName
from .models.stoppoint import StopPoint


class Store:
    """Base Store class."""

    def __init__(self, storepath: str) -> None:
        self.dat_dir = importlib.resources.files("lump")
        self.storepath = storepath
        self.data = {}

    def load(self) -> None:
        """Load the store data from file if exists otherwise query TfL."""
        if (self.dat_dir / (self.storepath + ".pkl")).is_file():
            with (self.dat_dir / (self.storepath + ".pkl")).open("rb") as datafile:
                self.data = pickle.load(datafile)
        else:
            self.data = self.fetch()

        self.save()

    def fetch(self) -> dict:
        """Fetch store data."""
        return {}

    def save(self) -> None:
        """Save the store data object using pickle."""
        with (self.dat_dir / (self.storepath + ".pkl")).open("wb") as lib_file:
            pickle.dump(self.data, lib_file)
            lib_file.close()

    def write_json(self) -> None:
        """Write the store data to a JSON file."""
        with (self.dat_dir / (self.storepath + ".json")).open(
            "w",
            newline="",
        ) as json_file:
            data_values = [stoppoint.model_dump() for stoppoint in self.data.values()]

            json.dump(data_values, json_file, ensure_ascii=False, indent=4, default=str)


class StopPointStore(Store):
    """A store of StopPoint instances keyed by NaPTAN ID."""

    def __init__(self) -> None:
        super().__init__("data/stoppoints")

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
        self.endpoint = f"/Line/Mode/{mode}/Route?serviceTypes=Regular,Night"

        if stop_point_store is None:
            self.stop_point_store = StopPointStore()
        else:
            self.stop_point_store = stop_point_store

        self.stop_point_store.load()

    def fetch(self) -> dict:
        """Fetch Line and Route data from TfL."""
        line_list = self.request(self.endpoint).json()

        for line_dict in line_list:
            if line_dict["id"] not in self.data:
                ## get sequence for each direction
                for section in line_dict["routeSections"]:
                    route_sequence = self._get_route_sequence(
                        line_dict["id"],
                        section["direction"],
                    )

                    section["isOutboundOnly"] = route_sequence.is_outbound_only
                    section["lineStrings"] = route_sequence.line_strings
                    section["orderedLineRoutes"] = route_sequence.ordered_line_routes

                ## parse route and add to store
                try:
                    line = Line.model_validate(line_dict)
                    self.data[line.id] = line
                except ValidationError as exc:
                    raise exc from exc

    def _get_route_sequence(self, line_id: str, direction: Direction) -> RouteSequence:
        """Fetch route sequence for given Line ID and Direction.

        Saves sequence StopPoint data to the owned StopPointStore.
        """
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
