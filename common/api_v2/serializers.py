from rest_framework import serializers


class CommonImportJobSerializer(serializers.Serializer[dict[str, object]]):
    type = serializers.ChoiceField(choices=["entity", "entry", "user", "group", "role"])
    job_ids = serializers.ListField(child=serializers.IntegerField())
    error = serializers.ListField(child=serializers.CharField())
