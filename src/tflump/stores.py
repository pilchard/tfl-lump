"""TfL Model Stores."""

from __future__ import annotations

import importlib
import json
import pickle
from pathlib import Path
from typing import TYPE_CHECKING

import httpx
import pandas as pd

from .client import get_tfl_client
from .config import get_settings
from .models.line import Line
from .models.route import RouteSequence
from .models.stoppoint import StopPoint, StopPointList

if TYPE_CHECKING:
    from .models.shared import ModeName

SETTINGS = get_settings()


class Store:
    """Base Store class."""

    def __init__(self, storename: str) -> None:
        self.datadir = importlib.resources.files("tflump")
        self.storename = storename
        self.data = {}

    # Pandas
    def dataframe(self) -> pd.Dataframe:
        """Return the store values as a Pandas DataFrame."""
        return pd.json_normalize(list(self.data.values()))

    # Lifecycle
    def load(self) -> None:
        """Load the store data from file if exists otherwise query TfL."""
        datafile = self.datadir / (self.storename + ".pkl")

        if datafile.is_file():
            with datafile.open("rb") as datafile:
                self.data = pickle.load(datafile)

        try:
            self._fetch()
        finally:
            self.save()

    def _fetch(self) -> dict:
        """Fetch store data."""

    def save(self, filename: str | None = None) -> None:
        """Save the store data object using pickle."""
        if filename is None:
            filepath = self.datadir / (self.storename + ".pkl")
        else:
            filepath = self.datadir / (filename + ".pkl")

        with filepath.open("wb") as lib_file:
            pickle.dump(self.data, lib_file)
            lib_file.close()

    # Output
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

    def __init__(self, storename: str = "data/stoppoints") -> None:
        super().__init__(storename)

    # Pandas
    def dataframe(self) -> pd.Dataframe:
        """Return the store values as a Pandas DataFrame."""
        return pd.json_normalize(list(self.data.values()))

    # Access
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
    """A store of Lines for a given Mode, keyed by Line ID."""

    def __init__(
        self,
        mode: ModeName,
        client: httpx.Client | None = None,
        stoppoint_store: StopPointStore | None = None,
    ) -> None:
        super().__init__(f"data/lines-{mode}")
        self.mode = mode

        if client is None:
            self.__client = get_tfl_client(
                app_id=SETTINGS.tfl.app_id,
                app_key=SETTINGS.tfl.app_key.get_secret_value(),
            )
        else:
            self.__client = client

        if stoppoint_store is None:
            self.__stoppoint_store = StopPointStore()
        else:
            self.__stoppoint_store = stoppoint_store

        self.__stoppoint_store.load()

    # Pandas
    def dataframe(self) -> pd.Dataframe:
        """Return the store values as a Pandas DataFrame."""
        return pd.json_normalize(list(self.data.values()))

    # Access
    def stoppoint_store(self) -> StopPointStore:
        return self.__stoppoint_store

    def has_line(self, line_id: str) -> bool:
        """Check if store includes Line."""
        return line_id in self.data

    def get_line(self, line_id: str) -> Line:
        """Return StopPoint for passed NaPTAN ID if it exists, otherwise None."""
        return self.data.get(line_id, None)

    def get_lines(self, line_ids: list[str]) -> list[Line]:
        """Return a list of Lines for passed Line IDs, missing ids will be replaced with None."""
        return [self.data.get(line_id, None) for line_id in line_ids]

    # Lifecycle
    def _fetch(self) -> dict:
        """Fetch Line and Route data from TfL.

        Fetches all lines and their route sections for the mode
        of the store. Also catalogs all stop points for each route
        section in the owned StopPointStore.

        On first run this is very slow due to the number of nested
        calls made. However on subsequent loads only lines not already
        in the store will be freshly queried.
        """
        # Fetch all lines for mode
        line_list = self.request(
            f"/Line/Mode/{self.mode}/Route?serviceTypes=Regular,Night",
        ).json()

        for line_dict in line_list:
            if line_dict["id"] not in self.data:
                ## get sequence for each direction
                for section in line_dict["routeSections"]:
                    seq_dict = self.request(
                        f"/Line/{line_dict["id"]}/Route/Sequence/{section["direction"]}",
                    ).json()

                    # Add StopPoints to store
                    for seq in seq_dict["stopPointSequences"]:
                        stop_points = StopPointList.model_validate(seq["stopPoint"])
                        self.__stoppoint_store.add_stop_points(
                            stop_points.model_dump(),
                        )

                    # merge sequence attributes into `route_section`
                    route_sequence = RouteSequence.model_validate(seq_dict)

                    section["isOutboundOnly"] = route_sequence.is_outbound_only
                    section["lineStrings"] = route_sequence.line_strings
                    section["orderedLineRoutes"] = route_sequence.ordered_line_routes

                # Parse line and index in store
                line = Line.model_validate(line_dict)
                self.data[line.id] = line.model_dump()

    def request(self, endpoint: str) -> httpx.Response:
        """Query TfL endpoint."""
        try:
            response = self.__client.get(endpoint)
            return response.raise_for_status()
        except httpx.RequestError as exc:
            print(f"An error occurred while requesting {exc.request.url!r}.")
            raise exc from exc
        except httpx.HTTPStatusError as exc:
            print(
                f"Error response {exc.response.status_code} while requesting {exc.request.url!r}.",
            )
            raise exc from exc
