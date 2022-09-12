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
