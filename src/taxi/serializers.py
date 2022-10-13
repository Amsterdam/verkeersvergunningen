import logging

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

log = logging.getLogger(__name__)


class OntheffingenRequestSerializer(serializers.Serializer):
    bsn = serializers.IntegerField()
    ontheffingsnummer = serializers.IntegerField()

    def validate_bsn(self, value):
        if not len(str(value)) == 9:
            raise ValidationError("The BSN number should be 9 digits")
        return value

    def validate_ontheffingsnummer(self, value):
        if not len(str(value)) == 7:
            raise ValidationError("The permit number should be 7 digits")
        return value


class HandhavingSerializer(serializers.Serializer):
    zaakidentificatie = serializers.CharField(max_length=40)
    geldigVanaf = serializers.DateTimeField()
    geldigTot = serializers.DateTimeField()


class OntheffingDetailSerializer(serializers.Serializer):
    ontheffingsnummer = serializers.CharField(max_length=40)
    geldigVanaf = serializers.DateTimeField()
    geldigTot = serializers.DateTimeField()
    schorsingen = HandhavingSerializer(many=True)


class OntheffingenResponseSerializer(serializers.Serializer):
    ontheffing = OntheffingDetailSerializer(many=True)
