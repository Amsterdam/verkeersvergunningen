from enum import Enum

from django.conf import settings


class DecosFolders(Enum):
    taxi = "TAXXXI"
    folders = (
        "FOLDERS"  # This may seem counterintuitive but one folder is called 'Folders'
    )


class DecosZaaknummers(Enum):
    """
    An enforcement case is a withdrawal of a permit, so if there is a permit and an
    enforcement case for that permit, the permit is invalidated
    """

    bsn = settings.TAXI_BSN_ZAAKNUMMER
    zone_ontheffing = settings.TAXI_ZONE_ONTHEFFING_ZAAKNUMMER  # Permits
    handhavingszaken = settings.TAXI_HANDHAVINGSZAKEN_ZAAKNUMMER  # Enforcement cases


class PermitParams(Enum):
    ontheffingsnummer = "sequence"
    zaakidentificatie = "key"
    geldigVanaf = "date6"
    geldigTot = "date7"
