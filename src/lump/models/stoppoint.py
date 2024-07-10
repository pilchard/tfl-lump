"""TfL StopPoint models."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import (
    AliasGenerator,
    BaseModel,
    ConfigDict,
    RootModel,
    field_validator,
    to_camel,
    to_snake,
)

if TYPE_CHECKING:
    from .line import Line
    from .shared import ModeName


class StopPoint(BaseModel):
    """Pydantic model for `Tfl-20` (`Tfl.Api.Presentation.Entities.MatchedStop`).

    see: https://api-portal.tfl.gov.uk/api-details#api=Line&operation=Line_RouteSequenceByPathIdPathDirectionQueryServiceTypesQueryExcludeCrowding&definition=Tfl-20

    Attributes
    ----------
    id : str

    stop_letter : str
        The stop letter, if it could be cleansed from the Indicator e.g. "K".

    name : str
        A human readable name.

    lat : float
        WGS84 latitude of the location.

    lon : float
        WGS84 longitude of the location.

    lines : list[int]
        A list of line ids that the stop point services.

    modes : list[ModeName]

    parent_id : str

    topMost_parent_id : str

    station_id : str
    """

    id: str
    stop_letter: str | None = None
    name: str
    lat: float
    lon: float
    lines: list[str]
    modes: list[ModeName]
    parent_id: str
    top_most_parent_id: str
    station_id: str

    model_config = ConfigDict(
        alias_generator=AliasGenerator(
            validation_alias=to_snake,
            serialization_alias=to_camel,
        ),
    )

    @field_validator("lines", mode="before")
    @classmethod
    def map_line_ids(cls, value: list[Line]) -> list[str]:
        """Return a list of line ids ."""
        return [line["id"] for line in value]


class StopPointList(RootModel):
    """A list of StopPoints."""

    root: list[StopPoint]
