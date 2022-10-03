import logging

from rest_framework import serializers

log = logging.getLogger(__name__)


class OntheffingenRequestSerializer(serializers.Serializer):
    bsn = serializers.IntegerField()


class HandhavingSerializer(serializers.Serializer):
    zaakidentificatie = serializers.CharField(max_length=40)
    geldigVanaf = serializers.DateTimeField()
    geldigTot = serializers.DateTimeField()


class OntheffingDetailResponseSerializer(serializers.Serializer):
    zaakidentificatie = serializers.CharField(max_length=40)
    geldigVanaf = serializers.DateTimeField()
    geldigTot = serializers.DateTimeField()
    schorsingen = HandhavingSerializer(many=True)


class OntheffingenResponseSerializer(serializers.Serializer):
    ontheffing = OntheffingDetailResponseSerializer(many=True)
