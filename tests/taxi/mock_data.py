from tests.utils import MockResponse


def mock_zaaknummer():
    return {
        "count": 1,
        "content": [
            {
                "key": '555aaa555',
                "fields": {
                    "num1": 123445
                },
                "links": [
                    {
                        "rel": "self",
                        "href": f"https://decosdvl.acc.amsterdam.nl/decosweb/aspx/api/v1/items/555aaa555"
                    }
                ]
            }
        ],
    }


def mock_handhavingszaken():
    return {
        "count": 1,
        "content": [
            {
                "key": "7CAAF40DB75A46BDB5CD5B2A948221B3",
                "fields": {},
                "links": [
                    {
                        "rel": "self",
                        "href": "https://decosdvl.acc.amsterdam.nl/decosweb/aspx/api/v1/items/7CAAF40DB75A46BDB5CD5B2A948221B3"
                    }
                ]
            }
        ],
        "links": [
            {
                "rel": "itemprofile",
                "href": "https://decosdvl.acc.amsterdam.nl/decosweb/aspx/api/v1/itemprofiles/007992321A8F49E9AF5041EDF1504F20%7C2E617BAF63B34D3C9606F92E59C9E09F/list"
            }
        ]
    }
