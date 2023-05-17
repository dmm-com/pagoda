import os
import sys
from typing import Any, Dict, List, TypedDict
import yaml
import configurations
from django.db.models import Model
from django.db.models.fields.related import ManyToManyField, ForeignKey
from django.db.models.fields import Field


# append airone directory to the default path
sys.path.append("./")

# prepare to load the data models of AirOne
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "airone.settings")
os.environ.setdefault("DJANGO_CONFIGURATION", "Dev")

# load AirOne application
configurations.setup()

from entry.models import LBVirtualServer, LBServiceGroup, LBPolicyTemplate, LBServer, Server  # NOQA


class EntryExportattr(TypedDict, total=False):
    name: str
    value: Any


class EntryExportEntry(TypedDict, total=False):
    name: str
    attrs: List[EntryExportattr]


class EntryExportData(TypedDict, total=False):
    entity: str
    entries: List[EntryExportEntry]


def set_test_data(entries: List[EntryExportEntry], model: Model, attribute: dict):
    attribute_info: Dict[str, Field] = {}
    for attr_name, field_name in attribute.items():
        attribute_info[attr_name] = model._meta.get_field(field_name)

    for entry in entries:
        (parent_instance, is_create) = model.objects.get_or_create(name=entry["name"])

        for attr in entry["attrs"]:
            if attr["name"] not in attribute_info.keys():
                continue

            if not attr["value"]:
                continue

            child_model = attribute_info[attr["name"]].related_model

            if isinstance(attribute_info[attr["name"]], ManyToManyField):
                child_instances = []
                for value in attr["value"]:
                    (child_instance, is_create) = child_model.objects.get_or_create(name=value)
                    child_instances.append(child_instance)
                manager = getattr(parent_instance, attribute_info[attr["name"]].attname)
                manager.add(*child_instances)
            elif isinstance(attribute_info[attr["name"]], ForeignKey):
                (child_instance, is_create) = child_model.objects.get_or_create(name=attr["value"])
                setattr(parent_instance, attribute_info[attr["name"]].attname, child_instance)
            else:
                setattr(parent_instance, attribute_info[attr["name"]].attname, attr["value"])

            parent_instance.save()


if __name__ == "__main__":
    data: List[EntryExportData]

    with open("/tmp/entry_LBVirtualServer.yaml", "r") as file:
        data = yaml.safe_load(file)
        set_test_data(
            data[0]["entries"],
            LBVirtualServer,
            {
                "LB": "lb",
                "IP Address": "ipaddr",
                "b-05 | 大分類": "large_category",
                "LBServiceGroup": "lb_service_group",
                "LBPolicyTemplate": "lb_policy_template",
            },
        )

    with open("/tmp/entry_LBPolicyTemplate.yaml", "r") as file:
        data = yaml.safe_load(file)
        set_test_data(
            data[0]["entries"],
            LBPolicyTemplate,
            {
                "LB": "lb",
                "LBServiceGroup": "lb_service_group",
            },
        )

    with open("/tmp/entry_LBServiceGroup.yaml", "r") as file:
        data = yaml.safe_load(file)
        set_test_data(
            data[0]["entries"],
            LBServiceGroup,
            {
                "LB": "lb",
                "LBServer": "lb_server",
            },
        )

    with open("/tmp/entry_LBServer.yaml", "r") as file:
        data = yaml.safe_load(file)
        set_test_data(
            data[0]["entries"],
            LBServer,
            {
                "LB": "lb",
                "IP Address": "ipaddr",
            },
        )

    with open("/tmp/entry_tsuchinoko-vm.yaml", "r") as file:
        data = yaml.safe_load(file)
        set_test_data(
            data[0]["entries"],
            Server,
            {
                "IP Addresses": "ipaddrs",
                "b-05 | 大分類": "large_category",
            },
        )
