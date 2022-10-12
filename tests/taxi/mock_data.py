def mock_driver():
    # curl -u 'DATAPUNT\API_TAXXXI:xxx' -H "accept:application/itemdata"
    # "https://decosdvl.acc.amsterdam.nl/decosweb/aspx/api/v1/items/
    # 1829F53FD9754B91ADC0B7D16E1519AD/TAXXXI?oDataQuery.filter=num1%20eq%20'233090125'"
    return {
        "count": 1,
        "content": [
            {
                "key": "07DAD65792F24AFEB59FF9D7028A6DD6",
                "fields": {
                    "num1": 233090125.00,
                    "text13": "12345678",
                    "text15": "Sener",
                    "text11": "654496832",
                    "initials": "KS",
                    "date7": "1983-07-22T00:00:00",
                    "text3": "Taxi Torro",
                    "text5": "P116146",
                    "text9": "123",
                    "num4": 6587435.00,
                },
            }
        ],
    }


def mock_ontheffing_driver():
    # curl -u 'DATAPUNT\API_TAXXXI:xxx' -H "accept:application/itemdata"
    # "https://decosdvl.acc.amsterdam.nl/decosweb/aspx/api/v1/items/
    # 07DAD65792F24AFEB59FF9D7028A6DD6/FOLDERS?oDataQuery.filter=
    # text45%20eq%20'TAXXXI%20Zone-ontheffing'%20and%20processed%20eq%20'true'%20and%20it_sequence%20eq%20'1978110'"
    return {
        "count": 1,
        "content": [
            {
                "key": "8E5F8EB000EC4938BC894CA2313E9134",
                "fields": {
                    "subject1": "Zone-ontheffing nieuw",
                    "date6": "2022-08-01T00:00:00",
                    "date7": "2025-07-31T00:00:00",
                    "dfunction": "Verleend",
                    "processed": True,
                    "mark": "Z/22/1978110",
                },
            }
        ],
    }


def mock_ontheffing_driver_empty():
    # curl -u 'DATAPUNT\API_TAXXXI:xxx' -H "accept:application/itemdata"
    # "https://decosdvl.acc.amsterdam.nl/decosweb/aspx/api/v1/items/
    # 07DAD65792F24AFEB59FF9D7028A6DD6/FOLDERS?oDataQuery.filter=
    # text45%20eq%20'TAXXXI%20Zone-ontheffing'%20and%20processed%20eq%20'true'%20and%20it_sequence%20eq%20'404'"
    return {
        "count": 0,
        "content": [],
    }


def mock_ontheffing_detail():
    # curl -u 'DATAPUNT\API_TAXXXI:xxx' -H "accept:application/itemdata"
    # "https://decosdvl.acc.amsterdam.nl/decosweb/aspx/api/v1/items/
    # D379EC92DE114A8E92A22FD0E7EFB4E6/FOLDERS?oDataQuery.filter=processed%20eq%20'true'%20
    # and%20it_sequence%20eq%20'1978110'"
    return {
        "count": 1,
        "content": [
            {
                "key": "8E5F8EB000EC4938BC894CA2313E9134",
                "fields": {
                    "sequence": 1978110.0,
                    "mark": "Z/22/1978110",
                    "processed": True,
                    "date6": "2022-08-01T00:00:00",
                    "date7": "2025-07-31T00:00:00",
                    "dfunction": "Verleend",
                    "text45": "Taxxxi Zone-ontheffing",
                },
            }
        ],
    }


def mock_ontheffing_detail_empty():
    # curl -u 'DATAPUNT\API_TAXXXI:xxx' -H "accept:application/itemdata"
    # "https://decosdvl.acc.amsterdam.nl/decosweb/aspx/api/v1/items/
    # D379EC92DE114A8E92A22FD0E7EFB4E6/FOLDERS?oDataQuery.filter=processed%20eq%20'true'%20
    # and%20it_sequence%20eq%20'404'"
    return {
        "count": 0,
        "content": [],
    }


def mock_handhavingen():
    # curl -u 'DATAPUNT\API_TAXXXI:xxx' -H "accept:application/itemdata"
    # "https://decosdvl.acc.amsterdam.nl/decosweb/aspx/api/v1/items/
    # 496E3E505C4045BAB5286B56CF2FC89E/FOLDERS?relTypeKey=8E5F8EB000EC4938BC894CA2313E9134"
    return {
        "count": 2,
        "content": [
            {
                "key": "7CAAF40DB75A46BDB5CD5B2A948221B3",
                "fields": {
                    "sequence": 1979535.0,
                    "mark": "Z/22/1979535",
                    "subject1": "Geen daklicht",
                    "processed": True,
                    "text45": "Taxxxi handhaving",
                    "date6": "2022-08-29T00:00:00",
                    "date7": "2022-09-28T00:00:00",
                    "dfunction": "Schorsen",
                },
            },
            {
                "key": "C06C49DC3BAA48E7A38C0D11F97D9770",
                "fields": {
                    "sequence": 1979576.0,
                    "mark": "Z/22/1979576",
                    "subject1": "Geen ID",
                    "processed": True,
                    "text45": "Taxxxi handhaving",
                    "date6": "2022-09-05T00:00:00",
                    "date7": "2022-09-26T00:00:00",
                }
            },
        ],
    }
