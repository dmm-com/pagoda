from typing import Any, TypedDict, Optional, List

from django.db.models import Prefetch
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from airone.lib.acl import ACLType

import custom_view
from airone.lib.types import AttrTypeValue, AttrDefaultValue
from entity.api_v2.serializers import EntitySerializer
from entity.models import Entity
from entry.models import Entry, Attribute
from group.models import Group
from job.models import Job
from user.models import User


class EntityAttributeType(TypedDict):
    id: int
    name: str


class EntryAttributeType(TypedDict):
    id: Optional[int]
    type: int
    value: Any
    schema: EntityAttributeType


class EntryBaseSerializer(serializers.ModelSerializer):
    schema = EntitySerializer(read_only=True)

    class Meta:
        model = Entry
        fields = ['id', 'schema', 'name']

    def _validate(self, name, schema, entity_attrs):
        # check name
        if name and Entry.objects.filter(name=name, schema=schema, is_active=True).exists():
            raise ValidationError("specified name(%s) already exists" % name)

        # check attrs mandatory attribute
        for mandatory_attr in schema.attrs.filter(is_mandatory=True, is_active=True):
            if mandatory_attr.id not in [attr['id'] for attr in entity_attrs]:
                raise ValidationError("mandatory attr(%s) is not specified" % mandatory_attr.name)

        # check attrs
        for entity_attr in entity_attrs:
            # check attrs id
            if not schema.attrs.filter(id=entity_attr['id']).exists():
                raise ValidationError("specified id(%s) does not exist" % entity_attr['id'])

            # TODO check attrs value
            # string, text: 'hoge'
            # entry, group: '9999'
            # named_entry: {'id': '9999', 'name': 'hoge'}
            # date: datetime.date(2022, 12, 31)
            # bool: True


class AttributeSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    value = serializers.ListField()


class EntryCreateSerializer(EntryBaseSerializer):
    schema = serializers.PrimaryKeyRelatedField(queryset=Entity.objects.all(), required=True)
    created_user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    attrs = serializers.ListField(child=AttributeSerializer(), write_only=True, required=False)

    class Meta:
        model = Entry
        fields = ['id', 'name', 'schema', 'created_user', 'attrs']

    def validate(self, params):
        self._validate(params['name'], params['schema'], params.get('attrs', []))
        return params

    def create(self, validated_data):
        user = User.objects.get(id=self.context['request'].user.id)

        entity_name = validated_data['schema'].name
        if custom_view.is_custom("before_create_entry", entity_name):
            custom_view.call_custom("before_create_entry", entity_name, user, validated_data)

        attrs_data = validated_data.pop('attrs', validated_data)
        entry = Entry.objects.create(**validated_data, status=Entry.STATUS_CREATING)

        for entity_attr in entry.schema.attrs.filter(is_active=True):
            attr = entry.add_attribute_from_base(entity_attr, user)

            # skip for unpermitted attributes
            if not user.has_permission(entity_attr, ACLType.Writable):
                continue

            # make an initial AttributeValue object if the initial value is specified
            attr_data = [x for x in attrs_data if int(x['id']) == entity_attr.id]
            if not attr_data:
                continue
            attr.add_value(user, attr_data['value'])

        if custom_view.is_custom("after_create_entry", entity_name):
            custom_view.call_custom("after_create_entry", entity_name, user, attrs_data, entry)

        # register entry information to Elasticsearch
        entry.register_es()

        # clear flag to specify this entry has been completed to ndcreate
        entry.del_status(Entry.STATUS_CREATING)

        # Send notification to the webhook URL
        job_notify_event = Job.new_notify_create_entry(user, entry)
        job_notify_event.run()

        return entry


class EntryUpdateSerializer(EntryBaseSerializer):
    attrs = serializers.ListField(child=AttributeSerializer(), write_only=True, required=False)

    class Meta:
        model = Entry
        fields = ['id', 'name', 'attrs']
        extra_kwargs = {
            'name': {'write_only': True, 'required': False},
        }

    def validate(self, params):
        self._validate(params.get('name', None), self.instance.schema, params.get('attrs', []))
        return params

    def update(self, entry: Entry, validated_data):
        attrs_data = validated_data.pop('attrs', validated_data)
        print(attrs_data)
        super().update(entry, validated_data)

        # TODO edit entry attrs

        return entry


class EntryRetrieveSerializer(EntryBaseSerializer):
    attrs = serializers.SerializerMethodField()

    class Meta:
        model = Entry
        fields = ['id', 'name', 'schema', 'is_active', 'attrs']
        read_only_fields = ['is_active']

    def get_attrs(self, obj: Entry) -> List[EntryAttributeType]:
        def get_attr_value(attr: Attribute):
            attrv = attr.get_latest_value(is_readonly=True)

            if not attrv:
                return ''

            if attr.schema.type & AttrTypeValue['array']:
                if attr.schema.type & AttrTypeValue['string']:
                    return [x.value for x in attrv.data_array.all()]

                elif attr.schema.type & AttrTypeValue['named']:
                    return [{
                        x.value: {
                            'id': x.referral.id if x.referral else None,
                            'name': x.referral.name if x.referral else '',
                            'schema': {
                                'id': x.referral.entry.schema.id,
                                'name': x.referral.entry.schema.name,
                            } if x.referral else {}
                        },
                    } for x in attrv.data_array.all()]

                elif attr.schema.type & AttrTypeValue['object']:
                    return [{
                        'id': x.referral.id if x.referral else None,
                        'name': x.referral.name if x.referral else '',
                        'schema': {
                            'id': x.referral.entry.schema.id,
                            'name': x.referral.entry.schema.name,
                        } if x.referral else {}
                    } for x in attrv.data_array.all()]

                elif attr.schema.type & AttrTypeValue['group']:
                    groups = [Group.objects.get(id=x.value) for x in attrv.data_array.all()]
                    return [{
                        'id': group.id,
                        'name': group.name,
                    } for group in groups]

            elif (attr.schema.type & AttrTypeValue['string'] or
                  attr.schema.type & AttrTypeValue['text']):
                return attrv.value

            elif attr.schema.type & AttrTypeValue['named']:
                return {
                    attrv.value: {
                        'id': attrv.referral.id if attrv.referral else None,
                        'name': attrv.referral.name if attrv.referral else '',
                        'schema': {
                            'id': attrv.referral.entry.schema.id,
                            'name': attrv.referral.entry.schema.name,
                        } if attrv.referral else {}
                    }
                }

            elif attr.schema.type & AttrTypeValue['object']:
                return {
                    'id': attrv.referral.id if attrv.referral else None,
                    'name': attrv.referral.name if attrv.referral else '',
                    'schema': {
                        'id': attrv.referral.entry.schema.id,
                        'name': attrv.referral.entry.schema.name,
                    } if attrv.referral else {}
                }

            elif attr.schema.type & AttrTypeValue['boolean']:
                return attrv.boolean

            elif attr.schema.type & AttrTypeValue['date']:
                return attrv.date

            elif attr.schema.type & AttrTypeValue['group'] and attrv.value:
                group = Group.objects.get(id=attrv.value)
                return {
                    'id': group.id,
                    'name': group.name,
                }

            else:
                return ''

        attr_prefetch = Prefetch(
            'attribute_set',
            queryset=Attribute.objects.filter(parent_entry=obj, is_active=True),
            to_attr="attr_list")
        entity_attrs = obj.schema.attrs.filter(is_active=True).prefetch_related(
            attr_prefetch).order_by('index')

        attrinfo: List[EntryAttributeType] = []
        for entity_attr in entity_attrs:
            attr = entity_attr.attr_list[0] if entity_attr.attr_list else None
            value = get_attr_value(attr) if attr else AttrDefaultValue[entity_attr.type]
            attrinfo.append({
                'id': attr.id if attr else None,
                'type': entity_attr.type,
                'value': value,
                'schema': {
                    'id': entity_attr.id,
                    'name': entity_attr.name,
                }
            })

        # add and remove attributes depending on entity
        if custom_view.is_custom("get_entry_attr", obj.schema.name):
            attrinfo = custom_view.call_custom("get_entry_attr", obj.schema.name, obj, attrinfo)

        return attrinfo


class GetEntrySimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Entry
        fields = ('id', 'name')
