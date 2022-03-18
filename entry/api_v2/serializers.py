from django.db.models import Prefetch

from airone.lib.types import AttrTypeValue, AttrDefaultValue
from entry.models import Entry, Attribute
from group.models import Group
from rest_framework import serializers
from typing import Any, Dict, TypedDict, Optional, List


class EntryAttributeType(TypedDict):
    id: Optional[int]
    type: int
    value: Any
    schema_id: int
    schema_name: str


class GetEntrySerializer(serializers.ModelSerializer):
    schema = serializers.SerializerMethodField()

    class Meta:
        model = Entry
        fields = ('id', 'name', 'schema')

    def get_schema(self, entry) -> Dict[str, Any]:
        return {
            'id': entry.schema.id,
            'name': entry.schema.name,
        }


class GetEntryWithAttrSerializer(GetEntrySerializer):
    schema = serializers.SerializerMethodField()
    attrs = serializers.SerializerMethodField()

    class Meta:
        model = Entry
        fields = ('id', 'name', 'schema', 'attrs')

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
                'schema_id': entity_attr.id,
                'schema_name': entity_attr.name,
            })

        return attrinfo


class GetEntrySimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Entry
        fields = ('id', 'name')
