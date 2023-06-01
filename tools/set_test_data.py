import os
import sys
from typing import Any, Dict, List, TypedDict
import yaml
import configurations
from django.db import connections
from django.db.models import Model
from django.db.models.fields.related import ManyToManyField, ForeignKey
from django.db.models.fields import Field
from django.conf import settings

# append airone directory to the default path
sys.path.append("./")

# prepare to load the data models of AirOne
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "airone.settings")
os.environ.setdefault("DJANGO_CONFIGURATION", "Dev")

# load AirOne application
configurations.setup()

from user_models.models import UserModel  # NOQA
from entity.models import Entity  # NOQA
from custom_view.lib.settings import ADAPTED_ENTITY  # NOQA


DEFAULT_DB = list(settings.DATABASES.keys())[-1]


class EntryExportattr(TypedDict, total=False):
    name: str
    value: Any


class EntryExportEntry(TypedDict, total=False):
    name: str
    attrs: List[EntryExportattr]


class EntryExportData(TypedDict, total=False):
    entity: str
    entries: List[EntryExportEntry]


def set_test_data(entries: List[EntryExportEntry], model: Model):
    attribute_info: Dict[str, Field] = {}
    for field in model._meta.get_fields():
        if not isinstance(field, Field):
            continue
        if field.attname in ["id", "name"]:
            continue
        attribute_info[field.verbose_name] = field

    for entry in entries:
        (parent_instance, is_create) = model.objects.get_or_create(name=entry["name"])

        for attr in entry["attrs"]:
            if attr["name"] not in attribute_info.keys():
                continue

            if not attr["value"]:
                continue

            child_model: Model = attribute_info[attr["name"]].related_model

            if isinstance(attribute_info[attr["name"]], ManyToManyField):
                m2m_model = attribute_info[attr["name"]].remote_field.through
                for value in attr["value"]:
                    if isinstance(value, dict):
                        for k, v in value.items():
                            if v is None:
                                continue
                            (child_instance, is_create) = child_model.objects.get_or_create(name=v)
                            m2m_model.objects.get_or_create(
                                **{
                                    "key": k,
                                    model._meta.model_name: parent_instance,
                                    child_model._meta.model_name: child_instance,
                                }
                            )
                    else:
                        (child_instance, is_create) = child_model.objects.get_or_create(name=value)
                        m2m_model.objects.get_or_create(
                            **{
                                model._meta.model_name: parent_instance,
                                child_model._meta.model_name: child_instance,
                            }
                        )
            elif isinstance(attribute_info[attr["name"]], ForeignKey):
                (child_instance, is_create) = child_model.objects.get_or_create(name=attr["value"])
                setattr(parent_instance, attribute_info[attr["name"]].attname, child_instance)
            else:
                setattr(parent_instance, attribute_info[attr["name"]].attname, attr["value"])

            parent_instance.save()


def create_django_models():
    name_map = {}
    for key, value in ADAPTED_ENTITY.items():
        if value.name is not None:
            name_map[value.name] = key

    model_map = {}
    for entity in Entity.objects.filter(is_active=True):
        print(entity.name)
        model = UserModel.create_model_from_entity(entity, name_map[entity.name])

        connection = connections[DEFAULT_DB]
        with connection.schema_editor() as se:
            try:
                sql, params = se.table_sql(model)
                print(sql)
                se.create_model(model)
            except Exception as e:
                print(e)

        model_map[entity.name] = model

    return model_map


if __name__ == "__main__":
    data: List[EntryExportData]

    # create Django Models from Entity information
    model_map = create_django_models()

    with open("/tmp/entry_LBVirtualServer.yaml", "r") as file:
        data = yaml.safe_load(file)
        set_test_data(data[0]["entries"], model_map["LBVirtualServer"])

    entity = Entity.objects.get(name="LBVirtualServer", is_active=True)
    model = UserModel.create_model_from_entity(entity)

    with open("/tmp/entry_LBPolicyTemplate.yaml", "r") as file:
        data = yaml.safe_load(file)
        set_test_data(data[0]["entries"], model_map["LBPolicyTemplate"])

    with open("/tmp/entry_LBServiceGroup.yaml", "r") as file:
        data = yaml.safe_load(file)
        set_test_data(data[0]["entries"], model_map["LBServiceGroup"])

    with open("/tmp/entry_LBServer.yaml", "r") as file:
        data = yaml.safe_load(file)
        set_test_data(data[0]["entries"], model_map["LBServer"])

    with open("/tmp/entry_tsuchinoko-vm.yaml", "r") as file:
        data = yaml.safe_load(file)
        set_test_data(data[0]["entries"], model_map["Server"])
