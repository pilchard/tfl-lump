"""TfL Shared Models."""

from enum import StrEnum
from typing import TypedDict


class TfL18(TypedDict):
    """Pydantic model for `TfL-18` (`Tfl.Api.Presentation.Entities.LineServiceTypeInfo`)."""  # noqa: E501

    name: str
    uri: str


class ServiceType(StrEnum):
    """Valid service types: "Regular" or "Night".

    All valid service types available from the `/Line/Meta/ServiceTypes` endpoint.

    The `/Mode/ActiveServiceTypes` endpoint will return the currently active
    service type for a mode (currently only supports `tube`).
    """

    REGULAR = "Regular"
    NIGHT = "Night"


class Direction(StrEnum):
    """Canonical direction: "inbound" or "outbound".

    The canonical direction between two stop points can be retrieved using the
    `/StopPoint/{id}/DirectionTo/{toStopPointId}[?lineId]` endpoint.
    """

    INBOUND = "inbound"
    OUTBOUND = "outbound"


class ModeName(StrEnum):
    """Mode names for the scheduled services operated by TfL.

    All valid modes available from the `/Line/Meta/Modes` endpoint.
    """

    BUS = "bus"
    CABLE_CAR = "cable-car"
    DLR = "dlr"
    ELIZABETH_LINE = "elizabeth-line"
    OVERGROUND = "overground"
    REPLACEMENT_BUS = "replacement-bus"
    RIVER_BUS = "river-bus"
    RIVER_TOUR = "river-tour"
    TRAM = "tram"
    TUBE = "tube"
