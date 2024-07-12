from .client import get_tfl_client
from .config import get_settings
from .models.line import Line, LineList
from .models.route import Route, Routelist, RouteSequence
from .models.shared import Direction, ModeName, ServiceType
from .models.stoppoint import StopPoint, StopPointList
from .stores import LineStore, StopPointStore

__version__ = "0.1.0"
__author__ = "Bryan Reedy"

COPYRIGHT_STATEMENT = """Powered by TfL Open Data. \
Contains OS data © Crown copyright and database rights 2016 \
and Geomni UK Map data © and database rights [2019]
"""
