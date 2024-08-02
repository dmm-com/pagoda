from datetime import datetime

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from airone.lib import custom_view
from airone.lib.types import AttrType
from entity.models import Entity
from entry.models import AttributeValue, Entry
from group.models import Group
from role.models import Role


class GetEntrySerializer(serializers.ModelSerializer):
    attrs = serializers.SerializerMethodField()

    class Meta:
        model = Entry
        fields = ("id", "name", "attrs")

    def get_attrs(self, obj):
        def get_attr_value(attr):
            attrv = attr.get_latest_value()

            if not attrv:
                return ""

            if attr.schema.type & AttrType._ARRAY:
                if attr.schema.type & AttrType.STRING:
                    return [x.value for x in attrv.data_array.all()]

                elif attr.schema.type & AttrType._NAMED:
                    return [
                        {
                            "name": x.value,
                            "ref_id": x.referral.id if x.referral else None,
                            "ref_name": x.referral.name if x.referral else "",
                        }
                        for x in attrv.data_array.all()
                    ]

                elif attr.schema.type & AttrType.OBJECT:
                    return [
                        {
                            "id": x.referral.id if x.referral else None,
                            "name": x.referral.name if x.referral else "",
                        }
                        for x in attrv.data_array.all()
                    ]

            elif attr.schema.type & AttrType.STRING or attr.schema.type & AttrType.TEXT:
                return attrv.value

            elif attr.schema.type & AttrType._NAMED:
                return {
                    "name": attrv.value,
                    "ref_id": attrv.referral.id if attrv.referral else None,
                    "ref_name": attrv.referral.name if attrv.referral else "",
                }

            elif attr.schema.type & AttrType.OBJECT:
                return {
                    "id": attrv.referral.id if attrv.referral else None,
                    "name": attrv.referral.name if attrv.referral else "",
                }

            elif attr.schema.type & AttrType.BOOLEAN:
                return attrv.boolean

            elif attr.schema.type & AttrType.DATE:
                return attrv.date

            elif attr.schema.type & AttrType.GROUP:
                group = attrv.group
                return {
                    "id": group.id,
                    "name": group.name,
                }

            elif attr.schema.type & AttrType.DATETIME:
                return attrv.datetime

        return [
            {
                "name": x.schema.name,
                "value": get_attr_value(x),
            }
            for x in obj.attrs.filter(is_active=True)
        ]


class PostEntrySerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    entity = serializers.CharField(required=True, max_length=100)
    name = serializers.CharField(required=True, max_length=100)
    attrs = serializers.DictField(required=True)

    def _validate_attr(self, attr, value):
        """This method validate and convert attribute value to be acceptable for AirOne"""

        def get_entry(schema, name):
            return Entry.objects.get(is_active=True, schema=schema, name=name)

        def is_entry(schema, name):
            return Entry.objects.filter(is_active=True, schema=schema, name=name)

        def validate_named_attr(value):
            if "name" not in value:
                value["name"] = ""

            if "id" not in value or not value["id"]:
                value["id"] = None
            else:
                entryset = [
                    get_entry(r, value["id"])
                    for r in attr.referral.all()
                    if is_entry(r, value["id"])
                ]

                # It means that there is no entry which is matched specified reference
                if not any(entryset):
                    return None

                value["id"] = entryset[0]

            return value

        if attr.type & AttrType._ARRAY:
            if not isinstance(value, list):
                return None

            if attr.type & AttrType.STRING:
                if not all(
                    [
                        isinstance(v, str) or isinstance(v, int) or isinstance(v, float)
                        for v in value
                    ]
                ):
                    return None
                return value

            elif attr.type & AttrType._NAMED:
                if not all([isinstance(v, dict) for v in value]):
                    return None

                return [x for x in [validate_named_attr(v) for v in value] if x]

            elif attr.type & AttrType.OBJECT:
                return sum(
                    [
                        [get_entry(r, v) for r in attr.referral.all() if is_entry(r, v)]
                        for v in value
                    ],
                    [],
                )

            elif attr.type & AttrType.GROUP:
                return [x for x in [AttributeValue.uniform_storable(v, Group) for v in value] if x]

            elif attr.type & AttrType.ROLE:
                return [x for x in [AttributeValue.uniform_storable(v, Role) for v in value] if x]

        elif attr.type & AttrType.STRING or attr.type & AttrType.TEXT:
            if not (isinstance(value, str) or isinstance(value, int) or isinstance(value, float)):
                return None
            return value

        elif attr.type & AttrType._NAMED:
            if not isinstance(value, dict):
                return None

            return validate_named_attr(value)

        elif attr.type & AttrType.OBJECT:
            if not value:
                # This means not None but empty referral value
                return 0

            if isinstance(value, str):
                entryset = [get_entry(x, value) for x in attr.referral.all() if is_entry(x, value)]
                if any(entryset):
                    return entryset[0]

            elif isinstance(value, int):
                return Entry.objects.filter(id=value, is_active=True).first()

        elif attr.type & AttrType.BOOLEAN:
            if not isinstance(value, bool):
                return None
            return value

        elif attr.type & AttrType.DATE:
            if isinstance(value, str):
                date_formats = ["%Y-%m-%d", "%Y/%m/%d"]  # List of acceptable date formats
                for date_format in date_formats:
                    try:
                        return datetime.strptime(value, date_format)
                    except ValueError:
                        continue  # Try the next format
                # If all formats failed, raise an error
                raise ValidationError("Incorrect data format, should be YYYY-MM-DD or YYYY/MM/DD")
            else:
                return None

        elif attr.type & AttrType.GROUP:
            return AttributeValue.uniform_storable(value, Group)

        elif attr.type & AttrType.ROLE:
            return AttributeValue.uniform_storable(value, Role)

        elif attr.type & AttrType.DATETIME:
            if isinstance(value, str):
                try:
                    datetime.fromisoformat(value)
                except ValueError:
                    raise ValueError("Incorrect data format, should be ISO8601 format")
                return datetime.fromisoformat(value)
            else:
                return None

        return None

    def validate(self, data):
        # checks specified entity is existed
        if not Entity.objects.filter(is_active=True, name=data["entity"]).exists():
            raise ValidationError("Invalid Entity is specified (%s)" % data["entity"])
        entity = data["entity"] = Entity.objects.get(is_active=True, name=data["entity"])

        entry = None
        if Entry.objects.filter(schema=entity, name=data["name"]).exists():
            entry = Entry.objects.get(schema=entity, name=data["name"])

        # checks specified entry-id is valid
        if "id" in data:
            if Entry.objects.filter(schema=entity, id=data["id"]).exists():
                entry = Entry.objects.get(schema=entity, id=data["id"])
            else:
                raise ValidationError("Invalid Entry-ID is specified (%d)" % data["id"])

        # checks mandatory keys are specified when a new Entry will be created
        if not entry and not all(
            [
                False
                for x in entity.attrs.filter(is_active=True, is_mandatory=True)
                if x.name not in data["attrs"].keys()
            ]
        ):
            raise ValidationError("Some mandatory attrs are not specified")

        # checks specified attr values are valid
        for attr_name, attr_value in data["attrs"].items():
            if not entity.attrs.filter(is_active=True, name=attr_name).exists():
                raise ValidationError("Target entity doesn't specified attr(%s)" % (attr_name))

            attr = entity.attrs.get(name=attr_name)
            validated_value = self._validate_attr(attr, attr_value)
            if validated_value is None:
                raise ValidationError("Invalid attribute value(%s) is specified" % (attr_name))

            data["attrs"][attr_name] = validated_value

        # check custom validate
        user = self.context["_user"]
        if custom_view.is_custom("validate_entry", entity.name):
            custom_view.call_custom(
                "validate_entry", entity.name, user, entity.name, data["name"], data["attrs"], entry
            )

        return data
