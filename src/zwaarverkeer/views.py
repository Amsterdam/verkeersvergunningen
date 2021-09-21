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


class GetPermitRequestSerializer(serializers.Serializer):
    number_plate = serializers.CharField(min_length=6, max_length=6)
    passage_at = serializers.DateTimeField()


class PermitSerializer(serializers.Serializer):
    permit_type = serializers.CharField(required=False, allow_null=True)
    permit_description = serializers.CharField(required=False)
    valid_from = serializers.DateTimeField(required=True)  # (required=False, allow_null=True)
    valid_until = serializers.DateTimeField(required=True)    # (required=False, allow_null=True)


class GetPermitsResponseSerializer(serializers.Serializer):
    number_plate = serializers.CharField(min_length=6, max_length=6)
    passage_at = serializers.DateTimeField()
    has_permit = serializers.BooleanField()
    permits = PermitSerializer(many=True)


class HasPermitView(CsrfExemptMixin, APIView):
    http_method_names = ['post']
    authentication_classes = [BasicAuthWithKeys]

    @swagger_auto_schema(
        request_body=GetPermitRequestSerializer,
        responses={200: GetPermitsResponseSerializer},  # TODO:Define more responses here
    )
    def post(self, request):
        req_ser = GetPermitRequestSerializer(data=request.data)
        if not req_ser.is_valid():
            # TODO: RETURN ERRORS CORRECTLY HERE
            return Response(req_ser.errors)

        number_plate = request.data['number_plate'].upper()
        passage_at = parser.parse(request.data['passage_at'])  # naive local datetime?

        try:
            decos = DecosJoin()
            permits = decos.get_permits(number_plate, passage_at)
            response = {
                'number_plate': number_plate,
                'passage_at': request.data['passage_at'],
                'has_permit': len(permits) > 0,
                'permits': permits,
            }
            ser = GetPermitsResponseSerializer(data=response)
            ser.is_valid(raise_exception=True)
            return Response(ser.data)

        except ImmediateHttpResponse as e:
            return e.response
        # TODO: also catch validation exception
        # TODO: test whether this also works with drf exception handling
