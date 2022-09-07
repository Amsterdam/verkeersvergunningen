import logging

from rest_framework import serializers

log = logging.getLogger(__name__)


class BsnRequestSerializer(serializers.Serializer):

    bsn = serializers.IntegerField()


class BsnRequestResponseSerializer(serializers.Serializer):

    pass
