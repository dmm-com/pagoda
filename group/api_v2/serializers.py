from typing import Dict, TypedDict

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from group.models import Group
from job.models import Job, JobOperation
from user.models import User


class GroupMemberType(TypedDict):
    id: int
    username: str


class GroupMemberSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()


class GroupSerializer(serializers.ModelSerializer):
    members = serializers.SerializerMethodField(method_name="get_members")

    class Meta:
        model = Group
        fields = ["id", "name", "parent_group", "members"]

    @extend_schema_field(GroupMemberSerializer(many=True))
    def get_members(self, obj: Group) -> list[GroupMemberType]:
        users = User.objects.filter(groups__name=obj.name, is_active=True).order_by("username")
        return [
            {
                "id": u.id,
                "username": u.username,
            }
            for u in users
        ]


class GroupCreateUpdateSerializer(serializers.ModelSerializer):
    members = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False
    )

    class Meta:
        model = Group
        fields = ["id", "name", "parent_group", "members"]

    def create(self, validated_data: Dict):
        parent_group = validated_data.get("parent_group")
        if parent_group and not parent_group.is_active:
            parent_group = None

        new_group = Group(
            name=validated_data["name"],
            parent_group=parent_group,
        )
        new_group.save()

        for user in [User.objects.get(id=x) for x in validated_data.get("members", [])]:
            user.groups.add(new_group)

        return new_group

    def update(self, instance: Group, validated_data: Dict):
        job_register_referrals = None
        if instance.name != validated_data["name"]:
            job_register_referrals = Job.new_register_referrals(
                self.context["request"].user,
                None,
                operation_value=JobOperation.GROUP_REGISTER_REFERRAL,
                params={"group_id": instance.id},
            )

        parent_group = validated_data.get("parent_group")
        if parent_group and not parent_group.is_active:
            parent_group = None

        # update group_name with specified one
        instance.name = validated_data["name"]
        instance.parent_group = parent_group
        instance.save()

        if job_register_referrals:
            job_register_referrals.run()

        # the processing for deleted users
        old_users = [str(x.id) for x in User.objects.filter(groups__id=instance.id, is_active=True)]
        for user in [
            User.objects.get(id=x) for x in set(old_users) - set(validated_data.get("members", []))
        ]:
            user.groups.remove(instance)

        # the processing for added users
        for user in [
            User.objects.get(id=x) for x in set(validated_data.get("members", [])) - set(old_users)
        ]:
            user.groups.add(instance)

        return instance


class GroupTreeSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField(method_name="get_children")

    class Meta:
        model = Group
        fields = ["id", "name", "children"]

    def get_children(self, obj: Group) -> list[Dict]:
        def _make_hierarchical_group(groups: list[Group]) -> list[Dict]:
            return [
                {
                    "id": g.id,
                    "name": g.name,
                    "children": _make_hierarchical_group(g.subordinates.filter(is_active=True)),
                }
                for g in groups
            ]

        return _make_hierarchical_group(obj.subordinates.filter(is_active=True))


class GroupImportSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    name = serializers.CharField()


class GroupExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ["id", "name"]
