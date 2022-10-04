from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from entity.models import Entity, EntityAttr
from entry.models import Entry


class AttrSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    value = serializers.CharField(max_length=200, required=False)
    is_any = serializers.BooleanField(required=False)
    attrs = serializers.ListField(required=False)

    def validate_name(self, name):
        if not EntityAttr.objects.filter(name=name, is_active=True).exists():
            raise ValidationError("There is no specified Attribute (%s)" % name)

        return name

    def validate_attrs(self, attrs):
        ret_data = []
        for attr_obj in attrs:
            obj = AttrSerializer(data=attr_obj)
            obj.is_valid()

            ret_data.append(obj.validated_data)

        return ret_data


class EntrySearchChainSerializer(serializers.Serializer):
    entities = serializers.ListField(child=serializers.CharField(max_length=200))
    attrs = serializers.ListField(child=AttrSerializer())
    is_any = serializers.BooleanField(required=False)

    def validate_entities(self, entities):
        ret_data = []
        for id_or_name in entities:
            if isinstance(id_or_name, int):
                if Entity.objects.filter(id=id_or_name, is_active=True).exists():
                    ret_data.append(id_or_name)

            elif isinstance(id_or_name, str):
                if (
                    id_or_name.isdecimal()
                    and Entity.objects.filter(id=int(id_or_name), is_active=True).exists()
                ):
                    ret_data.append(int(id_or_name))

                elif Entity.objects.filter(name=id_or_name, is_active=True).exists():
                    ret_data.append(Entity.objects.get(name=id_or_name, is_active=True).id)

        return ret_data

    def is_attr_chained(self, entry, attrs):
        # This is a helper method to check referral entry meets chaining conditions.
        def _is_attrv_referral_chained(attrv, info):
            chained_entry = Entry.objects.get(id=attrv.referral.id)
            if chained_entry is None or info['value'] not in chained_entry.name:
                return False

            if info.get('attrs'):
                return self.is_attr_chained(chained_entry, info['attrs'])
            else:
                return True

            return False

        for info in attrs:
            attrv = entry.get_attrv(info['name'])
            if not attrv:
                continue

            v = attrv.get_value(with_metainfo=True)
            if isinstance(v['value'], str) and info['value'] in v['value']:
                # this confirms text attribute value (e.g. AttrTypeValue['string'])
                # has expected value
                return True

            elif isinstance(v['value'], dict):
                # this confirms simple referral value (e.g. AttrTypeValue['object'])
                # has expected referral
                return _is_attrv_referral_chained(attrv, info)

            elif isinstance(v['value'], list):
                # this confirms array referral values (e.g. AttrTypeValue['array_object'])
                # has expected referral at least one
                for co_attrv in attrv.data_array.all():
                    if _is_attrv_referral_chained(co_attrv, info):
                        return True

        return False
