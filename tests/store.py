from lump import (
    LineStore,
    ModeName,
    StopPoint,
    StopPointStore,
    get_settings,
    get_tfl_client,
)

SETTINGS = get_settings()

if __name__ == "__main__":
    ## StopPointStore
    def test_sp_store() -> None:
        """StopPointStore simple testing."""
        sp_store = StopPointStore()
        sp_stub = """{"$type":"Tfl.Api.Presentation.Entities.MatchedStop,Tfl.Api.Presentation.Entities","parentId":"490G00010877","stationId":"490G00010877","icsId":"1010877","topMostParentId":"490G00010877","modes":["bus"],"stopType":"NaptanPublicBusCoachTram","stopLetter":"H","lines":[{"$type":"Tfl.Api.Presentation.Entities.Identifier,Tfl.Api.Presentation.Entities","id":"177","name":"177","uri":"/Line/177","type":"Line","crowding":{"$type":"Tfl.Api.Presentation.Entities.Crowding,Tfl.Api.Presentation.Entities"},"routeType":"Unknown","status":"Unknown"},{"$type":"Tfl.Api.Presentation.Entities.Identifier,Tfl.Api.Presentation.Entities","id":"381","name":"381","uri":"/Line/381","type":"Line","crowding":{"$type":"Tfl.Api.Presentation.Entities.Crowding,Tfl.Api.Presentation.Entities"},"routeType":"Unknown","status":"Unknown"},{"$type":"Tfl.Api.Presentation.Entities.Identifier,Tfl.Api.Presentation.Entities","id":"n381","name":"N381","uri":"/Line/n381","type":"Line","crowding":{"$type":"Tfl.Api.Presentation.Entities.Crowding,Tfl.Api.Presentation.Entities"},"routeType":"Unknown","status":"Unknown"},{"$type":"Tfl.Api.Presentation.Entities.Identifier,Tfl.Api.Presentation.Entities","id":"p12","name":"P12","uri":"/Line/p12","type":"Line","crowding":{"$type":"Tfl.Api.Presentation.Entities.Crowding,Tfl.Api.Presentation.Entities"},"routeType":"Unknown","status":"Unknown"},{"$type":"Tfl.Api.Presentation.Entities.Identifier,Tfl.Api.Presentation.Entities","id":"p13","name":"P13","uri":"/Line/p13","type":"Line","crowding":{"$type":"Tfl.Api.Presentation.Entities.Crowding,Tfl.Api.Presentation.Entities"},"routeType":"Unknown","status":"Unknown"}],"status":true,"id":"490010877H","name":"PeckhamBusStation","lat":51.473372,"lon":-0.067963}"""
        sp_store.add_stop_points([StopPoint.model_validate_json(sp_stub)])

        s1 = sp_store.get_stop_point("490010877H")
        print(s1)

        sp_store2 = StopPointStore()
        s2 = sp_store2.get_stop_point("490010877H")
        print(s2)

        sp_store2 = sp_store = None

    ## LineStore
    def test_l_store() -> None:
        """LineStore simple tests."""
        with get_tfl_client(
            app_id=SETTINGS.tfl.app_id,
            app_key=SETTINGS.tfl.app_key.get_secret_value(),
            max_requests=500,
            request_period=60,
        ) as client:
            sp_store = StopPointStore()
            l_store = LineStore(
                client=client,
                mode=ModeName.BUS,
                stop_point_store=sp_store,
            )

            l_store.load()

            print(len(sp_store.data))

            sp_store.write_json()
            l_store.write_json()


test_l_store()
