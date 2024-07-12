"""Store tests (rough)."""

from pathlib import Path

import pytest

from tflump import (
    LineStore,
    StopPoint,
    StopPointStore,
    get_tfl_client,
)


@pytest.mark.skip(reason="Messy overwrite issues.")
def test_stoppoint_store() -> None:
    """StopPointStore simple testing."""
    stoppoint_stub = """{"$type":"Tfl.Api.Presentation.Entities.MatchedStop,Tfl.Api.Presentation.Entities","parentId":"490G00010877","stationId":"490G00010877","icsId":"1010877","topMostParentId":"490G00010877","modes":["bus"],"stopType":"NaptanPublicBusCoachTram","stopLetter":"H","lines":[{"$type":"Tfl.Api.Presentation.Entities.Identifier,Tfl.Api.Presentation.Entities","id":"177","name":"177","uri":"/Line/177","type":"Line","crowding":{"$type":"Tfl.Api.Presentation.Entities.Crowding,Tfl.Api.Presentation.Entities"},"routeType":"Unknown","status":"Unknown"},{"$type":"Tfl.Api.Presentation.Entities.Identifier,Tfl.Api.Presentation.Entities","id":"381","name":"381","uri":"/Line/381","type":"Line","crowding":{"$type":"Tfl.Api.Presentation.Entities.Crowding,Tfl.Api.Presentation.Entities"},"routeType":"Unknown","status":"Unknown"},{"$type":"Tfl.Api.Presentation.Entities.Identifier,Tfl.Api.Presentation.Entities","id":"n381","name":"N381","uri":"/Line/n381","type":"Line","crowding":{"$type":"Tfl.Api.Presentation.Entities.Crowding,Tfl.Api.Presentation.Entities"},"routeType":"Unknown","status":"Unknown"},{"$type":"Tfl.Api.Presentation.Entities.Identifier,Tfl.Api.Presentation.Entities","id":"p12","name":"P12","uri":"/Line/p12","type":"Line","crowding":{"$type":"Tfl.Api.Presentation.Entities.Crowding,Tfl.Api.Presentation.Entities"},"routeType":"Unknown","status":"Unknown"},{"$type":"Tfl.Api.Presentation.Entities.Identifier,Tfl.Api.Presentation.Entities","id":"p13","name":"P13","uri":"/Line/p13","type":"Line","crowding":{"$type":"Tfl.Api.Presentation.Entities.Crowding,Tfl.Api.Presentation.Entities"},"routeType":"Unknown","status":"Unknown"}],"status":true,"id":"490010877H","name":"Peckham Bus Station","lat":51.473372,"lon":-0.067963}"""

    stoppoint_store = StopPointStore(storename="_test-stoppointstore")

    stoppoint_store.load()
    stoppoint = StopPoint.model_validate_json(stoppoint_stub).model_dump()
    stoppoint_store.add_stop_points([stoppoint])

    # StopPoint should be added
    assert stoppoint_store.get_stop_point("490010877H") == stoppoint


@pytest.fixture()
def testpath_fix():
    testpath = "./tests/linestore.json"

    yield testpath

    Path(testpath).unlink(missing_ok=True)


## LineStore
# @pytest.mark.usefixtures(testpath_fix)
def test_line_store(testpath_fix) -> None:
    """LineStore simple tests."""
    with get_tfl_client() as client:
        line_store = LineStore(
            client=client,
            mode="bus",
        )

        line_store.write_json(filepath=testpath_fix)

        # File should be added
        assert Path(testpath_fix).exists()
