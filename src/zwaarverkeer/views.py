import logging

from braces.views import CsrfExemptMixin
from dateutil import parser
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from zwaarverkeer.authentication import BasicAuthWithKeys
from zwaarverkeer.decos_join import DecosJoin
from zwaarverkeer.tools import ImmediateHttpResponse

log = logging.getLogger(__name__)


class HasPermitSerializer(serializers.Serializer):
    number_plate = serializers.CharField(min_length=6, max_length=6)
    passage_at = serializers.DateTimeField()


class HasPermitView(CsrfExemptMixin, APIView):
    http_method_names = ['post']
    authentication_classes = [BasicAuthWithKeys]
    serializer_classes = [HasPermitSerializer]
    # renderer_classes =

    def post(self, request):
        number_plate = request.data['number_plate']
        passage_at = parser.parse(request.data['passage_at'])  # naive local datetime?

        try:
            decos = DecosJoin()
            has_permit = decos.has_permit(number_plate, passage_at)
            return Response({'number_plate': request.data['number_plate'], 'has_permit': has_permit})
        except ImmediateHttpResponse as e:
            return e.response
