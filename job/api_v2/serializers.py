import math
from datetime import datetime, timezone
from typing import Optional, TypedDict

from rest_framework import serializers

from job.models import Job


class JobTarget(TypedDict):
    id: int
    name: str


class JobSerializers(serializers.ModelSerializer):
    target = serializers.SerializerMethodField(method_name="get_target")
    passed_time = serializers.SerializerMethodField(method_name="get_passed_time")

    class Meta:
        model = Job
        fields = ["id", "text", "status", "operation", "created_at", "target", "passed_time"]

    def get_target(self, obj: Job) -> Optional[JobTarget]:
        if obj.target is not None:
            return {
                "id": obj.target.id,
                "name": obj.target.name,
            }
        else:
            return None

    def get_passed_time(self, obj: Job) -> int:
        if obj.is_finished():
            return math.floor((obj.updated_at - obj.created_at).total_seconds())
        else:
            return math.floor((datetime.now(timezone.utc) - obj.created_at).total_seconds())
