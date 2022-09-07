import logging

from braces.views import CsrfExemptMixin
from dateutil import parser

from drf_yasg.utils import swagger_auto_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from main.authentication import BasicAuthWithKeys
from zwaarverkeer.serializers import PermitRequestSerializer, PermitsResponseSerializer
from zwaarverkeer.utils import DecosZwaarverkeer
from main.tools import ImmediateHttpResponse

log = logging.getLogger(__name__)


class PermitView(CsrfExemptMixin, APIView):
    http_method_names = ['post']
    authentication_classes = [BasicAuthWithKeys]

    @swagger_auto_schema(
        request_body=PermitRequestSerializer,
        responses={200: PermitsResponseSerializer},  # TODO:Define more responses here
    )
    def post(self, request):
        request_serializer = PermitRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)

        number_plate = request.data['number_plate'].upper()
        passage_at = parser.parse(request.data['passage_at'])  # naive local datetime?

        try:
            decos = DecosZwaarverkeer()
            permits = decos.get_permits(number_plate=number_plate, passage_at=passage_at)
            response = {
                'number_plate': number_plate,
                'passage_at': request.data['passage_at'],
                'has_permit': len(permits) > 0,
                'permits': permits,
            }
            response_serializer = PermitsResponseSerializer(data=response)
            response_serializer.is_valid(raise_exception=True)
            return Response(response_serializer.data)

        except ImmediateHttpResponse as e:
            return e.response
        # TODO: also catch validation exception
        # TODO: test whether this also works with drf exception handling
