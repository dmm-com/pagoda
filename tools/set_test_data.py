import os
import sys
from typing import Any, Dict, List, TypedDict
import yaml
import configurations
from django.db import models

# append airone directory to the default path
sys.path.append("./")

# prepare to load the data models of AirOne
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "airone.settings")
os.environ.setdefault("DJANGO_CONFIGURATION", "Dev")

# load AirOne application
configurations.setup()

from entry.models import (  # NOQA
    LBVirtualServer,
    LB,
    IPADDR,
    LargeCategory,
    LBServiceGroup,
    LBPolicyTemplate,
)


class EntryExportattr(TypedDict, total=False):
    name: str
    value: Any


class EntryExportEntry(TypedDict, total=False):
    name: str
    attrs: List[EntryExportattr]


class EntryExportData(TypedDict, total=False):
    entity: str
    entries: List[EntryExportEntry]


class AttributeInfo(TypedDict):
    model: models.Model
    key: str


def do_set_lb_virtual_server(lb_vsrv_instance: LBVirtualServer, lb_vsrv: EntryExportEntry):
    attribute_info: Dict[str, AttributeInfo] = {
        "LB": {"model": LB, "key": "lb"},
        "IP Address": {"model": IPADDR, "key": "ipaddr"},
        "b-05 | 大分類": {"model": LargeCategory, "key": "large_category"},
        "LBServiceGroup": {"model": LBServiceGroup, "key": "lb_service_group"},
        "LBPolicyTemplate": {"model": LBPolicyTemplate, "key": "lb_policy_template"},
    }
    for attr in lb_vsrv["attrs"]:
        if not attr["value"]:
            continue

        model = attribute_info[attr["name"]]["model"]

        if attr["name"] in ["LB", "IP Address", "b-05 | 大分類"]:
            (instance, is_create) = model.objects.get_or_create(name=attr["value"])
            setattr(lb_vsrv_instance, attribute_info[attr["name"]]["key"], instance)
        else:
            instances = []
            for value in attr["value"]:
                (instance, is_create) = model.objects.get_or_create(name=value)
                instances.append(instance)
            manager = getattr(lb_vsrv_instance, attribute_info[attr["name"]]["key"])
            manager.add(*instances)

        lb_vsrv_instance.save()


def set_test_data(entries: List[EntryExportEntry]):
    for lb_vsrv in entries:
        (lb_vsrv_instance, is_create) = LBVirtualServer.objects.get_or_create(name=lb_vsrv["name"])

        do_set_lb_virtual_server(lb_vsrv_instance, lb_vsrv)


if __name__ == "__main__":
    with open("/tmp/entry_LBVirtualServer.yaml", "r") as file:
        data: List[EntryExportData] = yaml.safe_load(file)

    set_test_data(data[0]["entries"])
