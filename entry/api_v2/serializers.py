from airone.lib.types import AttrTypeValue
from entry.models import Entry
from group.models import Group
from rest_framework import serializers
from typing import Any, Dict


class GetEntrySerializer(serializers.ModelSerializer):
    schema = serializers.SerializerMethodField()
    attrs = serializers.SerializerMethodField()

    class Meta:
        model = Entry
        fields = ('id', 'name', 'schema', 'attrs')

    def get_schema(self, entry) -> Dict[str, Any]:
        return {
                'id': entry.schema.id,
                'name': entry.schema.name,
        }

    def get_attrs(self, obj) -> Dict[str, Any]:
        def get_attr_value(attr):
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
                        },
                    } for x in attrv.data_array.all()]

                elif attr.schema.type & AttrTypeValue['object']:
                    return [{
                        'id': x.referral.id if x.referral else None,
                        'name': x.referral.name if x.referral else '',
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
                    }
                }

            elif attr.schema.type & AttrTypeValue['object']:
                return {
                    'id': attrv.referral.id if attrv.referral else None,
                    'name': attrv.referral.name if attrv.referral else '',
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

        return {
                x.schema.name: {
                    'id': x.id,
                    'type': x.schema.type,
                    'value': get_attr_value(x),
                    'schema_id': x.schema.id,
                }
                for x in obj.attrs.filter(is_active=True)}


class GetEntrySimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Entry
        fields = ('id', 'name')
