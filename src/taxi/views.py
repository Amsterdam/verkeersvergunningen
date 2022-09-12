import logging

from braces.views import CsrfExemptMixin
from django.http import HttpRequest
from drf_yasg.utils import swagger_auto_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from taxi.serializers import BsnRequestSerializer, BsnRequestResponseSerializer
from main.authentication import BasicAuthWithKeys
from main.utils import ImmediateHttpResponse
from taxi.utils import DecosTaxi

log = logging.getLogger(__name__)


class PermitView(CsrfExemptMixin, APIView):
    http_method_names = ['post']
    authentication_classes = [BasicAuthWithKeys]

    @swagger_auto_schema(
        request_body=BsnRequestSerializer,
        responses={200: BsnRequestResponseSerializer},  # TODO:Define more responses here
    )
    def post(self, request: HttpRequest):
        """
        Create a proxy request to decos for the taxi permits with the drivers
        bsn nr
        """
        serializer = BsnRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        bsn = serializer.validated_data['bsn']

        try:
            decos = DecosTaxi()
            return Response(data=decos.get_taxi_permit(bsn))

        except ImmediateHttpResponse as e:
            return e.response
        # TODO: also catch validation exception
        # TODO: test whether this also works with drf exception handling
