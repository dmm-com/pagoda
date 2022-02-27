from datetime import timedelta
from typing import Any, Dict, Optional

from rest_framework import serializers

from job.models import Job


class JobSerializer(serializers.ModelSerializer):
    target = serializers.SerializerMethodField(method_name='get_target')
    passed_time = serializers.SerializerMethodField(method_name='get_passed_time')

    class Meta:
        model = Job
        fields = ['id', 'text', 'status', 'operation', 'created_at', 'target', 'passed_time']

    def get_target(self, obj: Job) -> Optional[Dict[str, Any]]:
        if obj.target is not None:
            return {
                'id': obj.target.id,
                'name': obj.target.name,
            }
        else:
            return None

    def get_passed_time(self, obj: Job) -> timedelta:
        return obj.updated_at - obj.created_at
