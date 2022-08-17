from rest_framework import serializers

from job.models import Job


class JobSerializers(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = ["id", "status", "text"]
