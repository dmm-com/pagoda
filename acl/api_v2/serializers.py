from typing import Any, Dict, List, Optional
from rest_framework import serializers

from acl.models import ACLBase
from airone.lib.acl import ACLType
from entity.models import EntityAttr
from entry.models import Attribute
from group.models import Group
from user.models import User


class ACLSerializer(serializers.ModelSerializer):
    parent = serializers.SerializerMethodField(method_name='get_parent')
    acltypes = serializers.SerializerMethodField(method_name='get_acltypes')
    members = serializers.SerializerMethodField(method_name='get_members')

    class Meta:
        model = ACLBase
        fields = ['id', 'name', 'is_public', 'default_permission', 'objtype', 'parent', 'acltypes', 'members']

    def get_parent(self, obj: ACLBase) -> Optional[Any]:
        if isinstance(obj, Attribute):
            return obj.parent_entry
        elif isinstance(obj, EntityAttr):
            return obj.parent_entity
        else:
            return None

    def get_acltypes(self, obj: ACLBase) -> List[Dict[str, Any]]:
        return [{'id': x.id, 'name': x.label} for x in ACLType.all()]

    def get_members(self, obj: ACLBase) -> List[Dict[str, Any]]:
        # get ACLTypeID of target_obj if a permission is set
        def get_current_permission(member):
            permissions = [x for x in member.permissions.all() if x.get_objid() == obj.id]
            if permissions:
                return permissions[0].get_aclid()
            else:
                return 0

        return [{'id': x.id,
                 'name': x.username,
                 'current_permission': get_current_permission(x),
                 'type': 'user'} for x in User.objects.filter(is_active=True)] +\
               [{'id': x.id,
                 'name': x.name,
                 'current_permission': get_current_permission(x),
                 'type': 'group'} for x in Group.objects.filter(is_active=True)]
