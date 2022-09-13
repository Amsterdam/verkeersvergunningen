import logging

from rest_framework import serializers

log = logging.getLogger(__name__)


class OntheffingRequestSerializer(serializers.Serializer):
    bsn = serializers.IntegerField()


class OntheffingSerializer(serializers.Serializer):
    vergunningsnummer = serializers.CharField()


class OntheffingResponseSerializer(serializers.Serializer):
    permist = OntheffingSerializer(many=True)


# Serializers voor ontheffingen
class SchorsingenSerializer(serializers.Serializer):
    zaakidentificatie = serializers.CharField(max_length=40)
    geldigVanaf = serializers.DateField()
    geldigTot = serializers.DateField()


class HandhavingResponseSerializer(serializers.Serializer):
    ontheffingnummer = serializers.CharField(max_length=40)
    geldigVanaf = serializers.DateField()
    geldigTot = serializers.DateField()
    schorsingen = SchorsingenSerializer(many=True)
