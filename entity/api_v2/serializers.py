from airone.lib.acl import ACLType
from entity.models import Entity
from entry.models import Entry
from entry.settings import CONFIG as CONFIG_ENTRY
from rest_framework import serializers
from user.models import User


class EntitySerializer(serializers.ModelSerializer):
    entries = serializers.SerializerMethodField(method_name='get_entries')
    is_toplevel = serializers.SerializerMethodField(method_name='get_is_toplevel')
    attributes = serializers.SerializerMethodField(method_name='get_attributes')

    class Meta:
        model = Entity
        fields = ('id', 'name', 'note', 'is_toplevel', 'attributes', 'entries')

    def get_entries(self, entity: Entity):
        request = self.context.get('request')
        is_active = request.GET.get('is_active_entry', True) if request else True

        entries = Entry.objects.filter(schema=entity, is_active=is_active).order_by('name')
        return [{
            'id': e.id,
            'name': e.name,
            'status': e.status,
        } for e in entries[:CONFIG_ENTRY.MAX_LIST_ENTRIES]]

    def get_is_toplevel(self, entity: Entity):
        return (entity.status & Entity.STATUS_TOP_LEVEL) != 0

    def get_attributes(self, entity: Entity):
        request = self.context.get('request')
        user = User.objects.get(id=request.user.id)

        return [{
            'id': x.id,
            'name': x.name,
            'type': x.type,
            'is_mandatory': x.is_mandatory,
            'is_delete_in_chain': x.is_delete_in_chain,
            'referrals': [{
                'id': r.id,
                'name': r.name,
            } for r in x.referral.all()],
        } for x in entity.attrs.filter(is_active=True).order_by('index')
            if user.has_permission(x, ACLType.Writable)]
