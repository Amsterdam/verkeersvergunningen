import logging

from braces.views import CsrfExemptMixin
from django.http import HttpRequest
from drf_yasg.utils import swagger_auto_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from taxi.serializers import (
    OntheffingenRequestSerializer,
    OntheffingenResponseSerializer,
    OntheffingDetailResponseSerializer,
)
from main.authentication import BasicAuthWithKeys
from taxi.decos import DecosTaxi

log = logging.getLogger(__name__)


class OntheffingenBSNView(CsrfExemptMixin, APIView):
    http_method_names = ["post"]
    authentication_classes = [BasicAuthWithKeys]

    @swagger_auto_schema(
        request_body=OntheffingenRequestSerializer,
        responses={200: OntheffingenResponseSerializer},  # TODO:Define more responses here
    )
    def post(self, request: HttpRequest):
        """
        Create a proxy request to decos for the taxi permits with the drivers
        bsn nr
        """
        serializer = OntheffingenRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        bsn = serializer.validated_data["bsn"]
        decos = DecosTaxi()
        data = decos.get_ontheffingen_by_driver_bsn(driver_bsn=bsn)
        response_serializer = OntheffingenResponseSerializer(data={"ontheffing": data})
        response_serializer.is_valid(raise_exception=True)
        return Response(response_serializer.data)


class OntheffingDetailView(CsrfExemptMixin, APIView):
    http_method_names = ["get"]
    authentication_classes = [BasicAuthWithKeys]

    @swagger_auto_schema(
        responses={200: OntheffingDetailResponseSerializer},  # TODO:Define more responses here
    )
    def get(self, request, ontheffingsnummer: str):
        """
        create a proxy request to decos to query the 'handhavingen' permits
        Based on the 'ontheffingsnummer' retrieve all the 'handhavingen'
        """
        decos = DecosTaxi()
        data = decos.get_ontheffing_by_decos_key_ontheffing(ontheffing_decos_key=ontheffingsnummer)
        response_serializer = OntheffingDetailResponseSerializer(data=data)
        response_serializer.is_valid(raise_exception=True)
        return Response(response_serializer.data)
