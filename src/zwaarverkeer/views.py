import json
import logging
import os

import requests
from basicauth.decorators import basic_auth_required
from django.conf import settings
from django.http import HttpResponse, HttpResponseNotAllowed, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from zwaarverkeer.tools import ImmediateHttpResponse

log = logging.getLogger(__name__)


# def query_decos_for_number_plate(number_plate):
#     # TODO: also check for the date_from and the date_until of the vergunning
#     url = f"{settings.DECOS_BASE_URL}{settings.ZWAAR_VERKEER_ZAAKNUMMER}/FOLDERS?filter=TEXT48%20has%20'{number_plate}'%20and%20DFUNCTION%20eq%20'Verleend'%20and%20PROCESSED%20eq%20'J'"
#     breakpoint()
#     response = requests.get(url, auth=(settings.DECOS_BASIC_AUTH_USER, settings.DECOS_BASIC_AUTH_PASS))
#     return response.status_code == 200 and json.loads(response.content)['count'] >= 1


class DecosJoin:
    def __init__(self):
        self.base_url = settings.DECOS_BASE_URL
        self.zwaar_verkeer_zaaknr = settings.ZWAAR_VERKEER_ZAAKNUMMER
        self.auth_user = settings.DECOS_BASIC_AUTH_USER
        self.auth_pass = settings.DECOS_BASIC_AUTH_PASS

    def _build_url(self, *args):
        return os.path.join(self.base_url, settings.ZWAAR_VERKEER_ZAAKNUMMER, 'FOLDERS', *args)

    def _get_filters(self, number_plate):
        # TEXT48 = number_plate
        # DFUNCTION = result

        # TODO: also check for the date_from and the date_until of the vergunning
        filters = f"?filter=TEXT48 has '{number_plate}'" \
                  f" and PROCESSED eq 'J'" \
                  f" and DFUNCTION eq 'Verleend'"
        filters.replace(' ', '%20')
        return filters

    def _do_request(self, url):
        return requests.get(url, auth=(self.auth_user, self.auth_pass))

    def has_permit(self, number_plate):
        url = self._build_url(self._get_filters(number_plate))
        response = self._do_request(url)
        if response.status_code != 200:
            raise ImmediateHttpResponse(response=HttpResponse("We got an error response from Decos Join", status=502))
        return response.json()['count'] >= 1


@basic_auth_required
@csrf_exempt
def zwaar_verkeer(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(['POST'])

    try:
        number_plate = json.loads(request.body.decode("utf-8"))['number_plate']
        # TODO: check for number plate formatting for length and contains only numbers and letters
        # TODO: convert number_plate to UPPERCASE
        decos = DecosJoin()
        has_permit = decos.has_permit(number_plate)
        return JsonResponse(
            {
                'number_plate': number_plate,
                'has_permit': has_permit
            }
        )
    except ImmediateHttpResponse as e:
        return e.response
