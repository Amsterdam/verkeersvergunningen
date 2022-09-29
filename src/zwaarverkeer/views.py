import logging

import requests
from braces.views import CsrfExemptMixin
from dateutil import parser
from django.http import HttpResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from main.authentication import BasicAuthWithKeys
from zwaarverkeer.serializers import PermitsRequestSerializer, PermitsResponseSerializer
from zwaarverkeer.decos import DecosZwaarverkeer
from main.exceptions import ImmediateHttpResponse

log = logging.getLogger(__name__)


class PermitView(CsrfExemptMixin, APIView):
    http_method_names = ['post']
    authentication_classes = [BasicAuthWithKeys]

    @swagger_auto_schema(
        request_body=PermitsRequestSerializer,
        responses={200: PermitsResponseSerializer},  # TODO:Define more responses here
    )
    def post(self, request):
        request_serializer = PermitsRequestSerializer(data=request.data)
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
