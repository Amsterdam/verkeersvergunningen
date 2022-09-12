from requests import Request

from taxi.utils import DecosTaxi
import taxi
from .tools import MockResponse


def test_get_decos_key(mocker):
    DECOS_KEY = DecosTaxi.ZAAKNUMMER["BSN"]
    BSN_NUM = "233090125"
    expected_request_url = f"https://decosdvl.acc.amsterdam.nl/decosweb/aspx/api/v1/items/{DECOS_KEY}/TAXXXI?properties=false&fetchParents=false&oDataQuery.select=NUM1&oDataQuery.filter=NUM1%20eq%20%27{BSN_NUM}%27"
    decos_response = {
        "count": 1,
        "content": [
            {
                "key": DECOS_KEY,
                "fields": {
                    "num1": int(BSN_NUM)
                },
                "links": [
                    {
                        "rel": "self",
                        "href": "https://decosdvl.acc.amsterdam.nl/decosweb/aspx/api/v1/items/07DAD65792F24AFEB59FF9D7028A6DD6"
                    }
                ]
            }
        ],
        "links": [
            {
                "rel": "itemprofile",
                "href": "https://decosdvl.acc.amsterdam.nl/decosweb/aspx/api/v1/itemprofiles/D816614CA8C2451E8BDBFC6E31D9946E/list"
            }
        ]
    }
    mock_response = MockResponse(200, json_content=decos_response)
    mocker.patch('taxi.utils.DecosTaxi._get_response', return_value=mock_response)

    decos = DecosTaxi()
    decos_key = decos.get_decos_key(driver_bsn=BSN_NUM)

    # Check if the prepared url is correct
    mocked_response_function = taxi.utils.DecosTaxi._get_response
    call_args_kwargs = mocked_response_function.call_args.kwargs
    r = Request(**call_args_kwargs).prepare()
    assert r.url == expected_request_url
    # Check if the return value is parsed correctly
    assert decos_key == DECOS_KEY


def test_get_driver_permits(mocker):
    DECOS_KEY = "07DAD65792F24AFEB59FF9D7028A6DD6"
    PERMIT_1 = "7CAAF40DB75A46BDB5CD5B2A948221B3"
    PERMIT_2 = "8E5F8EB000EC4938BC894CA2313E9134"
    expected_request_url = f"https://decosdvl.acc.amsterdam.nl/decosweb/aspx/api/v1/items/{DECOS_KEY}/FOLDERS?properties=false&fetchParents=false&oDataQuery.select=DATE6%2CDATE7%2CPROCESSED%2CDFUNCTION%2CTEXT45&oDataQuery.filter=%28TEXT45%20eq%20%27TAXXXI%20Zone-ontheffing%27%20or%20TEXT45%20eq%20%27TAXXXI%20Handhaving%27%29"
    decos_response = {
        "count": 2,
        "content": [
            {
                "key": PERMIT_1,
                "fields": {
                    "isProcessed": True
                },
                "links": [
                    {
                        "rel": "self",
                        "href": f"https://decosdvl.acc.amsterdam.nl/decosweb/aspx/api/v1/items/{PERMIT_1}"
                    }
                ]
            },
            {
                "key": PERMIT_2,
                "fields": {
                    "isProcessed": True
                },
                "links": [
                    {
                        "rel": "self",
                        "href": f"https://decosdvl.acc.amsterdam.nl/decosweb/aspx/api/v1/items/{PERMIT_2}"
                    }
                ]
            }
        ],
        "links": [
            {
                "rel": "itemprofile",
                "href": "https://decosdvl.acc.amsterdam.nl/decosweb/aspx/api/v1/itemprofiles/D816614CA8C2451E8BDBFC6E31D9946E/list"
            }
        ]
    }
    mock_response = MockResponse(200, json_content=decos_response)
    mocker.patch('taxi.utils.DecosTaxi._get_response', return_value=mock_response)

    decos = DecosTaxi()
    permits = decos.get_driver_permits(driver_decos_key=DECOS_KEY)

    # Check if the prepared url is correct
    mocked_response_function = taxi.utils.DecosTaxi._get_response
    call_args_kwargs = mocked_response_function.call_args.kwargs
    r = Request(**call_args_kwargs).prepare()
    assert r.url == expected_request_url
    # Check if the return value is parsed correctly
    assert permits == [PERMIT_1, PERMIT_2]

