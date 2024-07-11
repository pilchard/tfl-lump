"""TfL StopPoint models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, RootModel, field_validator
from pydantic.alias_generators import to_camel

from .line import Line
from .shared import ModeName


class StopPoint(BaseModel):
    """Pydantic model for `Tfl-20` (`Tfl.Api.Presentation.Entities.MatchedStop`).

    see: https://api-portal.tfl.gov.uk/api-details#api=Line&operation=Line_RouteSequenceByPathIdPathDirectionQueryServiceTypesQueryExcludeCrowding&definition=Tfl-20

    Attributes
    ----------
    id : str

    stop_letter : str | None
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

    parent_id : str | None

    station_id : str | None

    topMost_parent_id : str | None
    """

    id: str
    stop_letter: str | None = None
    name: str
    lat: float
    lon: float
    lines: list[str]
    modes: list[ModeName]
    parent_id: str | None = None
    station_id: str | None = None
    top_most_parent_id: str | None = None

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
        use_enum_values=True,
    )

    @field_validator("lines", mode="before")
    @classmethod
    def map_line_ids(cls, value: list[Line]) -> list[str]:
        """Return a list of line ids ."""
        return [line["id"] for line in value]


class StopPointList(RootModel):
    """A list of StopPoints."""

    root: list[StopPoint]
