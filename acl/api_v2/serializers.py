from typing import Any, Dict, List, Optional
from rest_framework import serializers

from acl.models import ACLBase
from airone.lib.acl import ACLType, ACLObjType
from entity.models import EntityAttr, Entity
from entry.models import Attribute, Entry
from group.models import Group
from user.models import User


class ACLSerializer(serializers.ModelSerializer):
    parent = serializers.SerializerMethodField(method_name='get_parent', read_only=True)
    acltypes = serializers.SerializerMethodField(method_name='get_acltypes', read_only=True)
    members = serializers.SerializerMethodField(method_name='get_members', read_only=True)
    # TODO better name?
    acl = serializers.ListField(write_only=True)

    class Meta:
        model = ACLBase
        fields = ['id', 'name', 'is_public', 'default_permission', 'objtype', 'parent', 'acltypes',
                  'members', 'acl']

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

    def validate_default_permission(self, default_permission: int):
        return default_permission in ACLType.all()

    # TODO validate_permissions

    def update(self, instance, validated_data):
        acl_obj = getattr(self._get_acl_model(validated_data['objtype']),
                          'objects').get(id=instance.id)
        acl_obj.is_public = validated_data['is_public']
        acl_obj.default_permission = validated_data['default_permission']
        acl_obj.save()

        for item in [x for x in validated_data['acl'] if x['value']]:
            if item['member_type'] == 'user':
                member = User.objects.get(id=item['member_id'])
            else:
                member = Group.objects.get(id=item['member_id'])
            acl_type = [x for x in ACLType.all() if x == int(item['value'])][0]

            # update permissios for the target ACLBased object
            self._set_permission(member, acl_obj, acl_type)

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
    def _set_permission(member, acl_obj, acl_type):
        # clear unset permissions of target ACLbased object
        for _acltype in ACLType.all():
            if _acltype != acl_type and _acltype != ACLType.Nothing:
                member.permissions.remove(getattr(acl_obj, _acltype.name))

        # set new permissoin to be specified except for 'Nothing' permission
        if acl_type != ACLType.Nothing:
            member.permissions.add(getattr(acl_obj, acl_type.name))
