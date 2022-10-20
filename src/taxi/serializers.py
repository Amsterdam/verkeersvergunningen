import logging

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

log = logging.getLogger(__name__)


class OntheffingenRequestSerializer(serializers.Serializer):
    bsn = serializers.CharField(min_length=9, max_length=9)
    ontheffingsnummer = serializers.CharField(min_length=7, max_length=7)

    def validate_bsn(self, value):
        if not value.isdigit():
            raise ValidationError("The BSN number should be 9 digits")
        return value

    def validate_ontheffingsnummer(self, value):
        if not value.isdigit():
            raise ValidationError("The permit number should be 7 digits")
        return value


class HandhavingSerializer(serializers.Serializer):
    zaakidentificatie = serializers.CharField(max_length=40)
    geldigVanaf = serializers.DateField()
    geldigTot = serializers.DateField()


class OntheffingResponseSerializer(serializers.Serializer):
    ontheffingsnummer = serializers.CharField(max_length=40)
    geldigVanaf = serializers.DateField()
    geldigTot = serializers.DateField()
    schorsingen = HandhavingSerializer(many=True)


class OntheffingenResponseSerializer(serializers.Serializer):
    ontheffing = OntheffingResponseSerializer(many=True)
