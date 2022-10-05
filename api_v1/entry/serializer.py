from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from entity.models import Entity, EntityAttr
from entry.models import Entry


class AttrSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    value = serializers.CharField(max_length=200, required=False, allow_blank=True)
    is_any = serializers.BooleanField(required=False, default=False)
    attrs = serializers.ListField(required=False)

    def validate_name(self, name):
        if not EntityAttr.objects.filter(name=name, is_active=True).exists():
            raise ValidationError("There is no specified Attribute (%s)" % name)

        return name

    def validate_attrs(self, attrs):
        ret_data = []
        for attr_obj in attrs:
            obj = AttrSerializer(data=attr_obj)
            if not obj.is_valid():
                raise ValidationError("Failed to validate attrs query (%s)" % str(attr_obj))

            ret_data.append(obj.validated_data)

        return ret_data


class EntrySearchChainSerializer(serializers.Serializer):
    entities = serializers.ListField(child=serializers.CharField(max_length=200))
    attrs = serializers.ListField(child=AttrSerializer())
    is_any = serializers.BooleanField(required=False, default=False)

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

    def is_attr_chained(self, entry, attrs=None, is_any=False):
        if not attrs:
            attrs = self.validated_data["attrs"]
            is_any = self.validated_data["is_any"]

        # This is a helper method to check referral entry meets chaining conditions.
        def _is_attrv_referral_chained(attrv, info):
            chained_entry = Entry.objects.get(id=attrv.referral.id)
            if chained_entry is None and info.get("value") == "":
                # The case when Attribute value doesn't refer Entry and query expects it is
                return True

            elif chained_entry is not None and info.get("value") == "":
                # The case when Attribute value refers actual Entry but query expects it's blank
                return False

            elif chained_entry is None or info.get("value", "") not in chained_entry.name:
                # The case when Attribute value deons't refer, or
                # referred Entry is not expected one.
                return False

            elif info.get("attrs"):
                return self.is_attr_chained(chained_entry, info["attrs"], info["is_any"])

            return not info["is_any"]

        for info in attrs:
            attrv = entry.get_attrv(info["name"])
            if not attrv:
                if is_any:
                    continue
                else:
                    # In this case, it doesn't meet specified condition at least one.
                    # Then, there is no nocessity to check rest of query any more
                    # when is_any parameter is False (it means AND condition).
                    return False

            v = attrv.get_value(with_metainfo=True)
            if isinstance(v["value"], str) and info.get("value", "") in v["value"]:
                # This confirms text attribute value (e.g. AttrTypeValue['string'])
                # has expected value. It returns True when the "is_any" parameter
                # is True (it means OR condition).
                if is_any:
                    return True

            elif isinstance(v["value"], dict):
                # this confirms simple referral value (e.g. AttrTypeValue['object'])
                # has expected referral
                condition = _is_attrv_referral_chained(attrv, info)
                if not condition and not is_any:
                    # This returns False immediately whenever it doesn't meet specified
                    # conditions at least one when the "is_any" parameter is False
                    # (it means AND condition).
                    return False

                elif condition and is_any:
                    # This returns True immediately whenever it doesn't meet specified
                    # conditions at least one when the "is_any" parameter is True
                    # (it means OR condition).
                    return True

            elif isinstance(v["value"], list):
                # This is a termination condition when Attribute value refers no Entry.
                if not attrv.data_array.exists() and info.get("value") != "" and not is_any:
                    # This returns False immediately whenever there is no attribute value
                    # when the "is_any" parameter is False (it means AND condition).
                    # except for the case when query expects this Attribute value doesn't
                    # refer any Entries
                    return False

                elif attrv.data_array.exists():
                    # This variable (is_matched) is necessary for AND condition.
                    # We couldn't determine whether search is faileda until all co-Attribute
                    # value have been checked. It should return False when all co-Attribute
                    # values wouldn't meet specified condition if "is_any" parameter is False
                    # (it means AND condition).
                    is_matched = False
                    for co_attrv in attrv.data_array.all():
                        condition = _is_attrv_referral_chained(co_attrv, info)
                        if condition:
                            is_matched = True

                            # This returns True immediately whenever it doesn't meet specified
                            # conditions at least one when the "is_any" parameter is True
                            # (it means OR condition).
                            if is_any:
                                return True

                    if not is_matched and not is_any:
                        return False

        # This returns False when "is_any" parameter is True (it means OR condition), because
        # the query results didn't meet any specified conditions (it means there is no Entry
        # that matches specified query).
        # In opposiet, this returns True when "is_any" parameter is False (it means AND condition)
        # because, result matches all specified conditions.
        return not is_any
