import math
from datetime import datetime, timezone
from typing import Any, TypedDict

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from airone.lib.acl import ACLObjType
from entry.models import Entry
from job.models import Job
from user.models import User


class JobTarget(TypedDict):
    id: int
    name: str
    schema_id: int | None
    schema_name: str | None


class JobTargetSerializer(serializers.Serializer[JobTarget]):
    id = serializers.IntegerField()
    name = serializers.CharField()
    schema_id = serializers.IntegerField(allow_null=True)
    schema_name = serializers.CharField(allow_null=True)


class JobSerializers(serializers.ModelSerializer[Job]):
    user: serializers.SlugRelatedField[User] = serializers.SlugRelatedField(
        slug_field="username", read_only=True
    )
    target = serializers.SerializerMethodField(method_name="get_target")
    passed_time = serializers.SerializerMethodField(method_name="get_passed_time")

    PREFETCHED_ENTRIES_KEY = "__prefetched_entries"

    class Meta:
        model = Job
        fields = [
            "id",
            "user",
            "text",
            "status",
            "operation",
            "created_at",
            "target",
            "passed_time",
        ]

    @extend_schema_field(JobTargetSerializer())
    def get_target(self, obj: Job) -> JobTarget | None:
        if obj.target is not None:
            if obj.target.objtype == ACLObjType.Entry:
                sub: dict[str, Any] = self.context.get(self.PREFETCHED_ENTRIES_KEY, {}).get(
                    obj.target.id
                )
                if not sub:
                    sub = dict(
                        Entry.objects.filter(id=obj.target.id)
                        .select_related("schema")
                        .values("id", "name", "schema__id", "schema__name")
                        .first()
                        or {}
                    )
                return {
                    "id": sub["id"],
                    "name": sub["name"],
                    "schema_id": sub["schema__id"],
                    "schema_name": sub["schema__name"],
                }
            else:
                return {
                    "id": obj.target.id,
                    "name": obj.target.name,
                    "schema_id": None,
                    "schema_name": None,
                }
        else:
            return None

    def get_passed_time(self, obj: Job) -> int:
        if obj.is_finished(with_refresh=False):
            return math.floor((obj.updated_at - obj.created_at).total_seconds())
        else:
            return math.floor((datetime.now(timezone.utc) - obj.created_at).total_seconds())


class ImportPreviewChangeSerializer(serializers.Serializer[dict[str, Any]]):
    field = serializers.CharField()
    before = serializers.CharField(allow_null=True)
    after = serializers.CharField(allow_null=True)


class ImportPreviewRowSerializer(serializers.Serializer[dict[str, Any]]):
    index = serializers.IntegerField()
    kind = serializers.CharField(help_text="What the row describes, e.g. Entity or EntityAttr")
    name = serializers.CharField()
    action = serializers.ChoiceField(choices=["create", "update", "unchanged", "skip", "error"])
    reason = serializers.CharField(allow_null=True)
    changes = ImportPreviewChangeSerializer(many=True)
    will_invoke_trigger = serializers.BooleanField(
        help_text="True when importing this row would fire a TriggerAction"
    )


class ImportPreviewSummarySerializer(serializers.Serializer[dict[str, Any]]):
    # Past tense because "create"/"update" would shadow BaseSerializer.create()/update().
    created = serializers.IntegerField()
    updated = serializers.IntegerField()
    unchanged = serializers.IntegerField()
    skipped = serializers.IntegerField()
    errored = serializers.IntegerField()
    total = serializers.IntegerField()


class ImportPreviewSerializer(serializers.Serializer[dict[str, Any]]):
    summary = ImportPreviewSummarySerializer()
    rows = ImportPreviewRowSerializer(many=True)
    count = serializers.IntegerField(help_text="Number of rows available to list")
    truncated = serializers.BooleanField(
        help_text="True when the summary covers more rows than can be listed"
    )


class ImportPreviewJobSerializer(serializers.Serializer[dict[str, Any]]):
    job_id = serializers.IntegerField(help_text="Poll this job, then read its preview")


class ImportPreviewJobForEntitySerializer(ImportPreviewJobSerializer):
    entity = serializers.CharField(help_text="The model whose items this preview covers")


class ImportPreviewJobsResultSerializer(serializers.Serializer[dict[str, Any]]):
    jobs = ImportPreviewJobForEntitySerializer(many=True)
    error = serializers.ListField(child=serializers.CharField())


class ImportPreviewJobsSerializer(serializers.Serializer[dict[str, Any]]):
    """One preview job per model, mirroring the shape of the item import API."""

    result = ImportPreviewJobsResultSerializer()
