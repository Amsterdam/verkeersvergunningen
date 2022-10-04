from taxi.enums import PermitParams


def mock_driver():
    return {
        "count": 1,
        "content": [
            {
                "key": "555aaa555",
                "fields": {"num1": 123445},
                "links": [
                    {"rel": "self", "href": f"https://decosdvl.acc.amsterdam.nl/decosweb/aspx/api/v1/items/555aaa555"}
                ],
            }
        ],
    }


def mock_handhavingszaken():
    return {
        "count": 2,
        "content": [
            {
                "key": "7CAAF40DB75A46BDB5CD5B2A948221B3",
                "fields": {
                    "date6": "2022-08-29T00:00:00",
                    "date7": "2022-09-28T00:00:00",
                    "dfunction": "Schorsen",
                },
            },
            {
                "key": "C06C49DC3BAA48E7A38C0D11F97D9770",
                "fields": {"date6": "2022-09-05T00:00:00", "date7": "2022-09-26T00:00:00"},
            },
        ],
    }


def mock_parsed_enforcement_cases():
    return [
            {
                PermitParams.zaakidentificatie.name: "7CAAF40DB75A46BDB5CD5B2A948221B3",
                PermitParams.geldigVanaf.name: "2022-08-29T00:00:00",
                PermitParams.geldigTot.name: "2022-09-28T00:00:00",
            },
            {
                PermitParams.zaakidentificatie.name: "C06C49DC3BAA48E7A38C0D11F97D9770",
                PermitParams.geldigVanaf.name: "2022-09-05T00:00:00",
                PermitParams.geldigTot.name: "2022-09-26T00:00:00",
            }
        ]


def mock_permits():
    return {
        "count": 2,
        "content": [
            {
                "key": "7CAAF40DB75A46BDB5CD5B2A948221B3",
                "fields": {"date6": "2022-08-29T00:00:00", "date7": "2022-09-28T00:00:00", "dfunction": "Schorsen"},
                "links": [
                    {
                        "rel": "self",
                        "href": "https://decosdvl.acc.amsterdam.nl/decosweb/aspx/api/v1/items/7CAAF40DB75A46BDB5CD5B2A948221B3",
                    }
                ],
            },
            {
                "key": "C06C49DC3BAA48E7A38C0D11F97D9770",
                "fields": {"date6": "2022-09-05T00:00:00", "date7": "2022-09-26T00:00:00"},
                "links": [
                    {
                        "rel": "self",
                        "href": "https://decosdvl.acc.amsterdam.nl/decosweb/aspx/api/v1/items/C06C49DC3BAA48E7A38C0D11F97D9770",
                    }
                ],
            },
        ],
        "links": [
            {
                "rel": "itemprofile",
                "href": "https://decosdvl.acc.amsterdam.nl/decosweb/aspx/api/v1/itemprofiles/007992321A8F49E9AF5041EDF1504F20|2E617BAF63B34D3C9606F92E59C9E09F/list",
            }
        ],
    }
