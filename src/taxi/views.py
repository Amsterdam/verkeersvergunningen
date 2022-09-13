import logging

from braces.views import CsrfExemptMixin
from django.http import HttpRequest
from drf_yasg.utils import swagger_auto_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from taxi.serializers import OntheffingRequestSerializer, \
    OntheffingResponseSerializer, HandhavingResponseSerializer
from main.authentication import BasicAuthWithKeys
from main.utils import ImmediateHttpResponse
from taxi.utils import DecosTaxi

log = logging.getLogger(__name__)


class OntheffingView(CsrfExemptMixin, APIView):
    http_method_names = ['post']
    authentication_classes = [BasicAuthWithKeys]

    @swagger_auto_schema(
        request_body=OntheffingRequestSerializer,
        responses={200: OntheffingResponseSerializer},  # TODO:Define more responses here
    )
    def post(self, request: HttpRequest):
        """
        Create a proxy request to decos for the taxi permits with the drivers
        bsn nr
        """
        serializer = OntheffingRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        bsn = serializer.validated_data['bsn']

        try:
            decos = DecosTaxi()
            data = decos.get_taxi_zone_ontheffing(bsn)
            response_serializer = \
                OntheffingResponseSerializer(data={'ontheffing': data})
            response_serializer.is_valid(raise_exception=True)
            return Response(response_serializer.data)

        except ImmediateHttpResponse as e:
            return e.response
        # TODO: also catch validation exception
        # TODO: test whether this also works with drf exception handling


class HandhavingView(CsrfExemptMixin, APIView):
    http_method_names = ['get']
    # authentication_classes = [BasicAuthWithKeys]

    @swagger_auto_schema(
        responses={200: HandhavingResponseSerializer},  # TODO:Define more responses here
    )
    def get(self, request, ontheffingsnummer: str):
        """
        create a proxy request to decos to query the "handhavingen" permits
        """
        try:
            decos = DecosTaxi()
            return Response(data=decos.get_handhavingzaken(ontheffingsnummer))

        except ImmediateHttpResponse as e:
            return e.response
        # TODO: also catch validation exception
        # TODO: test whether this also works with drf exception handling