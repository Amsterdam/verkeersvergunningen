import logging

from braces.views import CsrfExemptMixin
from dateutil import parser
from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from zwaarverkeer.authentication import BasicAuthWithKeys
from zwaarverkeer.decos_join import DecosJoin
from zwaarverkeer.tools import ImmediateHttpResponse

log = logging.getLogger(__name__)


class HasPermitRequestSerializer(serializers.Serializer):
    number_plate = serializers.CharField(min_length=6, max_length=6)
    passage_at = serializers.DateTimeField()


class HasPermitResponseSerializer(serializers.Serializer):
    number_plate = serializers.CharField(min_length=6, max_length=6)
    passage_at = serializers.DateTimeField()
    has_permit = serializers.BooleanField()
    permit_type = serializers.CharField(required=False, allow_null=True)
    date_from = serializers.DateTimeField(required=False, allow_null=True)
    date_until = serializers.DateTimeField(required=False, allow_null=True)


class HasPermitView(CsrfExemptMixin, APIView):
    http_method_names = ['post']
    authentication_classes = [BasicAuthWithKeys]

    @swagger_auto_schema(
        request_body=HasPermitRequestSerializer,
        responses={200: HasPermitResponseSerializer},  # Define more responses here
    )
    def post(self, request):
        req_ser = HasPermitRequestSerializer(data=request.data)
        if not req_ser.is_valid():
            # RETURN ERRORS CORRECTLY HERE
            return Response(req_ser.errors)

        number_plate = request.data['number_plate'].upper()
        passage_at = parser.parse(request.data['passage_at'])  # naive local datetime?

        try:
            decos = DecosJoin()
            has_permit, permit_type = decos.get_permit(number_plate, passage_at)
            response = {
                'number_plate': number_plate,
                'passage_at': request.data['passage_at'],
                'has_permit': has_permit,
                'permit_type': permit_type,
                'date_from': None,
                'date_until': None,
            }
            ser = HasPermitResponseSerializer(data=response)
            ser.is_valid(raise_exception=True)
            return Response(ser.data)

        except ImmediateHttpResponse as e:
            return e.response
