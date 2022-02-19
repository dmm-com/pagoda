from rest_framework import serializers

from job.models import Job


class JobSerializer(serializers.ModelSerializer):
    target = serializers.SerializerMethodField(method_name='get_target')
    passed_time = serializers.SerializerMethodField(method_name='get_passed_time')

    class Meta:
        model = Job
        fields = ['id', 'text', 'status', 'operation', 'created_at', 'target', 'passed_time']

    def get_target(self, obj: Job):
        return {
            'id': obj.target.id,
            'name': obj.target.name,
        }

    def get_passed_time(self, obj: Job):
        return obj.updated_at - obj.created_at
