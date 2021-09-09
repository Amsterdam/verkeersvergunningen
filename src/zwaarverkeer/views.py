import json
import logging

from basicauth.decorators import basic_auth_required
from django.http import HttpResponseNotAllowed, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from zwaarverkeer.decos_join import DecosJoin
from zwaarverkeer.tools import ImmediateHttpResponse
from django.http import HttpResponse

log = logging.getLogger(__name__)


@basic_auth_required
@csrf_exempt
def zwaar_verkeer(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(['POST'])

    try:
        number_plate = json.loads(request.body.decode("utf-8"))['number_plate']
        # TODO: check for number plate formatting (len and isalnum) and upper
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
    except json.decoder.JSONDecodeError as e:
        return HttpResponse("Invalid JSON", status=400)
