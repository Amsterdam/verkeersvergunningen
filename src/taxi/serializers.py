import logging

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

log = logging.getLogger(__name__)


class OntheffingenRequestSerializer(serializers.Serializer):
    bsn = serializers.IntegerField()

    def validate_bsn(self, value):
        if not (value.isdigit() and len(value) == 9):
            raise ValidationError("The BSN number should be 9 digits")
        return value


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
