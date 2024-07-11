"""TfL Route Models."""

from __future__ import annotations

from datetime import datetime
from typing import TypedDict

from pydantic import (
    BaseModel,
    ConfigDict,
    RootModel,
    field_validator,
)
from pydantic.alias_generators import to_camel

from .shared import Direction, ServiceType


class TfL22(TypedDict):
    """Pydantic model for `TfL-22` (`Tfl.Api.Presentation.Entities.OrderedRoute`)."""

    name: str
    naptan_ids: list[str]
    service_type: ServiceType

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
        use_enum_values=True,
    )


class RouteSequence(BaseModel):
    """Pydantic model for `Tfl-23` (`Tfl.Api.Presentation.Entities.StopPointSequence`).

    Minimal representation of Tfl-23 to be appended to Route model.

    see: https://api-portal.tfl.gov.uk/api-details#api=Line&operation=Line_RouteSequenceByPathIdPathDirectionQueryServiceTypesQueryExcludeCrowding&definition=Tfl-23

    Attributes
    ----------
    is_outbound_only : bool | None

    line_strings : list[str]
        A list of JSON encoded linestrings

    ordered_line_routes : list[str]
        An list of NaPTAN ids sorted in order of arrival for the route. (`Tfl-22.naptanIds`)
    """

    is_outbound_only: bool | None = None
    line_strings: list[str]
    ordered_line_routes: list[list[str]]

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
        use_enum_values=True,
    )

    @field_validator("ordered_line_routes", mode="before")
    @classmethod
    def map_naptan_ids(cls, value: list[TfL22]) -> list[list[str]]:
        """Return only the `naptanIds` property."""
        return [lineRoute["naptanIds"] for lineRoute in value]


class Route(BaseModel):
    """Pydantic model for `Tfl-17` (`Tfl.Api.Presentation.Entities.MatchedRoute`).

    Description of a Route used in Route search results.

    see: https://api-portal.tfl.gov.uk/api-details#api=Line&operation=Line_LineRoutesByIdsByPathIdsQueryServiceTypes&definition=Tfl-17

    Attributes
    ----------
    name : str
        Name such as "72"

    direction : Direction

    origination_name : str
        The name of the Origin StopPoint.

    destination_name : str
        The name of the Destination StopPoint.

    originator : str
        The Id (NaPTAN code) of the Origin StopPoint.

    destination : str
        The Id (NaPTAN code) or the Destination StopPoint.

    serviceType : ServiceType

    valid_to : datetime
        (date-time) The DateTime that the Service containing this Route is valid until.

    valid_from : datetime
        (date-time) The DateTime that the Service containing this Route is valid from.

    is_outbound_only : bool
        Merged from RouteSequence (`Tfl-23`).

    line_strings : list[str]
        A list of JSON encoded linestrings.
        Merged from RouteSequence (`Tfl-23`).

    ordered_line_routes : list[str]
        Merged from RouteSequence (`Tfl-23`).
    """

    name: str
    direction: Direction
    origination_name: str
    destination_name: str
    originator: str
    destination: str
    service_type: ServiceType
    valid_to: datetime
    valid_from: datetime
    is_outbound_only: bool
    line_strings: list[str]
    ordered_line_routes: list[list[str]]

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
        use_enum_values=True,
    )


class Routelist(RootModel):
    """A list of Routes."""

    root: list[Route]
