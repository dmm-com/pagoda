from typing import Any, Dict, List, Optional

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from acl.models import ACLBase
from airone.lib.acl import ACLObjType, ACLType
from entity.models import Entity, EntityAttr
from entry.models import Attribute, Entry
from group.models import Group
from role.models import Role
from user.models import User


class ACLSerializer(serializers.ModelSerializer):
    parent = serializers.SerializerMethodField(method_name="get_parent", read_only=True)
    acltypes = serializers.SerializerMethodField(method_name="get_acltypes", read_only=True)
    members = serializers.SerializerMethodField(method_name="get_members", read_only=True)
    roles = serializers.SerializerMethodField(method_name="get_roles", read_only=True)
    # TODO better name?
    acl = serializers.ListField(write_only=True)

    class Meta:
        model = ACLBase
        fields = [
            "id",
            "name",
            "is_public",
            "default_permission",
            "objtype",
            "parent",
            "acltypes",
            "members",
            "acl",
            "roles",
        ]

    def get_parent(self, obj: ACLBase) -> Optional[Any]:
        if isinstance(obj, Attribute):
            return obj.parent_entry
        elif isinstance(obj, EntityAttr):
            return obj.parent_entity
        else:
            return None

    def get_acltypes(self, obj: ACLBase) -> List[Dict[str, Any]]:
        return [{"id": x.id, "name": x.label} for x in ACLType.all()]

    def get_members(self, obj: ACLBase) -> List[Dict[str, Any]]:
        # get ACLTypeID of target_obj if a permission is set
        def get_current_permission(member):
            permissions = [x for x in member.permissions.all() if x.get_objid() == obj.id]
            if permissions:
                return permissions[0].get_aclid()
            else:
                return 0

        return [
            {
                "id": x.id,
                "name": x.username,
                "current_permission": get_current_permission(x),
                "type": "user",
            }
            for x in User.objects.filter(is_active=True)
        ] + [
            {
                "id": x.id,
                "name": x.name,
                "current_permission": get_current_permission(x),
                "type": "group",
            }
            for x in Group.objects.filter(is_active=True)
        ]

    def get_roles(self, obj: ACLBase) -> List[Dict[str, Any]]:
        user = self.context["request"].user

        return [
            {
                "id": x.id,
                "name": x.name,
                "description": x.description,
                "current_permission": x.get_current_permission(obj),
            }
            for x in Role.objects.filter(is_active=True)
            if user.is_superuser or x.is_belonged_to(user)
        ]

    def validate_default_permission(self, default_permission: int):
        return default_permission in ACLType.all()

    def validate(self, attrs: Dict[str, Any]):
        # validate acl paramter
        for acl_info in attrs["acl"]:
            if "member_id" not in acl_info:
                raise ValidationError('"member_id" parameter is necessary for "acl" parameter')

            role = Role.objects.filter(id=acl_info["member_id"]).first()
            if not role:
                raise ValidationError("Invalid member_id of Role instance is specified")

        user = self.context["request"].user
        if not user.is_permitted_to_change(
            self.instance,
            ACLType.Full,
            **{
                "will_be_public": attrs["is_public"],
                "default_permission": attrs["default_permission"],
                "acl_settings": [
                    {
                        "role": Role.objects.filter(id=x["member_id"], is_active=True).first(),
                        "value": int(x["value"]),
                    }
                    for x in attrs["acl"]
                ],
            }
        ):
            raise ValidationError(
                "Inadmissible setting." "By this change you will never change this ACL"
            )

        return attrs

    def update(self, instance, validated_data):
        acl_obj = getattr(self._get_acl_model(validated_data["objtype"]), "objects").get(
            id=instance.id
        )
        acl_obj.is_public = validated_data["is_public"]
        acl_obj.default_permission = validated_data["default_permission"]
        acl_obj.save()

        for item in [x for x in validated_data["acl"] if x["value"]]:
            role = Role.objects.get(id=item["member_id"])
            acl_type = [x for x in ACLType.all() if x == int(item["value"])][0]

            # update permissios for the target ACLBased object
            self._set_permission(role, acl_obj, acl_type)

        return acl_obj

    @staticmethod
    def _get_acl_model(object_id):
        if int(object_id) == ACLObjType.Entity:
            return Entity
        if int(object_id) == ACLObjType.Entry:
            return Entry
        elif int(object_id) == ACLObjType.EntityAttr:
            return EntityAttr
        elif int(object_id) == ACLObjType.EntryAttr:
            return Attribute
        else:
            return ACLBase

    @staticmethod
    def _set_permission(role, acl_obj, acl_type):
        # clear unset permissions of target ACLbased object
        for _acltype in ACLType.all():
            if _acltype != acl_type and _acltype != ACLType.Nothing:
                role.permissions.remove(getattr(acl_obj, _acltype.name))

        # set new permissoin to be specified except for 'Nothing' permission
        if acl_type != ACLType.Nothing:
            role.permissions.add(getattr(acl_obj, acl_type.name))
