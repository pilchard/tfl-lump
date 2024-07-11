"""TfL Line Model."""

from __future__ import annotations

from pydantic import (
    BaseModel,
    ConfigDict,
    RootModel,
    field_validator,
)
from pydantic.alias_generators import to_camel

from .route import Route
from .shared import ModeName, ServiceType, TfL18


class Line(BaseModel):
    """Pydantic model for `Tfl-19` (`Tfl.Api.Presentation.Entities.Line`).

    see: https://api-portal.tfl.gov.uk/api-details#api=Line&operation=Line_GetByModeByPathModes&definition=Tfl-19

    Attributes
    ----------
    id : str

    name : str

    modeName : ModeName

    routeSections : list[Route]

    serviceTypes : list[ServiceType]
    """

    id: str
    name: str
    mode_name: ModeName
    route_sections: list[Route]
    service_types: list[ServiceType]

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
        use_enum_values=True,
    )

    @field_validator("service_types", mode="before")
    @classmethod
    def map_service_types(cls, value: list[TfL18]) -> list[ServiceType]:
        """Return a list of valid service types."""
        return [
            ServiceType(serviceType["name"])
            for serviceType in value
            if serviceType["name"] in ServiceType._value2member_map_
        ]


class LineList(RootModel):
    """A list of Lines."""

    root: list[Line]
