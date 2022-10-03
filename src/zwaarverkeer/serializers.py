from rest_framework import serializers


class PermitsRequestSerializer(serializers.Serializer):
    number_plate = serializers.CharField(min_length=6, max_length=6)
    passage_at = serializers.DateTimeField()


class PermitSerializer(serializers.Serializer):
    permit_type = serializers.CharField(required=False, allow_null=True)
    permit_description = serializers.CharField(required=False)
    valid_from = serializers.DateTimeField(required=True)
    valid_until = serializers.DateTimeField(required=True)


class PermitsResponseSerializer(serializers.Serializer):
    number_plate = serializers.CharField(min_length=6, max_length=6)
    passage_at = serializers.DateTimeField()
    has_permit = serializers.BooleanField()
    permits = PermitSerializer(many=True)
