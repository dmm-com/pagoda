from typing import Optional
from django.forms import CharField
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.request import Request
from django.db.models import Prefetch, Q
from django.db import models
from acl.models import ACLBase
from airone.lib.drf import InvalidValueError, ObjectNotExistsError, RequiredParameterError
from airone.lib.types import AttrTypeValue
from entry.models import Entry, Attribute, AttributeValue, LBVirtualServer, LBServiceGroup
from entity.models import Entity, EntityAttr
from user_models.models import DRFGenerator, UserModel

from . import serializers


class AirOnePageNumberPagination(PageNumberPagination):
    page_size_query_param = "page_size"


class OriginAdvancedSearchSQLAPI(ReadOnlyModelViewSet):
    serializer_class = serializers.AdvancedSearchSQLSerializer
    pagination_class = AirOnePageNumberPagination
    queryset = (
        LBVirtualServer.objects.all()
        .prefetch_related(
            "lb_policy_template__lb_service_group__m2mlbservicegrouplbserver_set__lbserver__ipaddr__server_set__large_category",
            "lb_service_group__m2mlbservicegrouplbserver_set__lbserver__ipaddr__server_set__large_category",
            "ipaddr__server_set__large_category",
        )
        .select_related("lb", "large_category")
    )


class SimpleAdvancedSearchSQLAPI(ReadOnlyModelViewSet):
    serializer_class = serializers.LBSerializer
    pagination_class = AirOnePageNumberPagination
    queryset = LBServiceGroup.objects.all()


class AdvancedSearchSQLAPI(ReadOnlyModelViewSet):
    pagination_class = AirOnePageNumberPagination

    def get_serializer_class(self):
        # create DRF Serializer Class frmo Django model dynamically
        serializer_class = DRFGenerator.serializer.create(
            self._airone_model, getting_fields=["id", "name", "attrs"]
        )

        return serializer_class

    def get_queryset(self):
        entity_name = self.request.query_params.get("entity", None)
        if not entity_name:
            raise RequiredParameterError("entity parameter is required")

        model = UserModel.create_model_from_entity(
            Entity.objects.get(name=entity_name, is_active=True)
        )
        # save created model to use it for creating Serializer class
        self._airone_model = model

        return model.objects.all()


class AdvancedSearchAPI(ReadOnlyModelViewSet):
    serializer_class = serializers.AdvancedSearchSerializer
    pagination_class = AirOnePageNumberPagination

    def _validate_query_params(self, request: Request):
        entity_name = request.query_params.get("entity", None)
        if not entity_name:
            raise RequiredParameterError("entity parameter is required")

        entity = Entity.objects.filter(name=entity_name, is_active=True).first()
        if not entity:
            raise ObjectNotExistsError("specified entity does not exist")

        query = request.query_params.get("query", None)
        if not query:
            return

        for pair in query.split():
            if ":" not in pair:
                raise InvalidValueError("specified query parameter format is invalid")
            attr_name, value = pair.split(":")
            if not entity.attrs.filter(name=attr_name, is_active=True).exists():
                raise InvalidValueError(
                    "specified query parameter attr(%s) does not exist" % attr_name
                )
            if not value:
                raise InvalidValueError("specified query parameter value is required")

    def list(self, request: Request, *args, **kwargs):
        self._validate_query_params(request)
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        try:
            self._validate_query_params(self.request)
        except Exception:
            return []

        entity_name = self.request.query_params.get("entity", None)
        query = self.request.query_params.get("query", None)

        entity = Entity.objects.get(name=entity_name, is_active=True)

        attrv_prefetch = Prefetch(
            "values",
            AttributeValue.objects.filter(is_latest=True)
            .select_related("referral__schema")
            .prefetch_related("data_array__referral__schema"),
        )
        attr_prefetch = Prefetch(
            "attrs",
            Attribute.objects.filter(schema__is_active=True).prefetch_related(attrv_prefetch),
        )

        refer_prefetch = Prefetch(
            "referred_attr_value",
            AttributeValue.objects.filter(
                is_latest=True,
                parent_attr__schema__is_active=True,
                parent_attr__parent_entry__is_active=True,
            ).prefetch_related("parent_attr__parent_entry__schema"),
        )

        if query:
            attr_infos = {}
            for pair in query.split():
                key, value = pair.split(":")
                attr_infos[key] = value
        else:
            return (
                Entry.objects.filter(schema=entity, is_active=True)
                .order_by("name")
                .select_related("schema")
                .prefetch_related(attr_prefetch, refer_prefetch)
            )

        target_entries = None
        for attr_name, value in attr_infos.items():
            entity_attr = EntityAttr.objects.get(
                parent_entity=entity, name=attr_name, is_active=True
            )
            query = Q(parent_attr__schema=entity_attr)
            if entity_attr.type & AttrTypeValue["object"]:
                query = Q(query, referral__name__regex=value)
            else:
                query = Q(query, value__regex=value)

            entries = AttributeValue.objects.filter(query).values_list(
                "parent_attr__parent_entry", flat=True
            )

            # at first loop, set value
            if not target_entries:
                target_entries = entries

            target_entries = set(target_entries) & set(entries)

        return Entry.objects.filter(id__in=target_entries).order_by("name")

    def list_tmp(self, request, *args, **kwargs):
        def _get_value(value: Optional[AttributeValue], attr_infos):
            return {
                "value": value.value if value else "",
                "referral": _get_entry(value.referral, attr_infos)
                if value and value.referral
                else None,
            }

        def _get_entry(entry: Entry, attr_infos):
            ret_entry = {
                "id": entry.id,
                "name": entry.name,
                "schema": {
                    "id": entry.schema.id,
                    "name": entry.schema.name,
                },
            }
            if attr_infos == []:
                return ret_entry

            ret_entry["attrs"] = []

            for attr_info in attr_infos:
                attrs = getattr(entry, attr_info["name"])
                if not attrs:
                    continue
                attrv: AttributeValue = attrs[0].values.all()[0]
                value = []
                if attr_info["is_array"]:
                    for co_attrv in attrv.data_array.all():
                        value.append(_get_value(co_attrv, attr_info["childs"]))
                else:
                    value.append(_get_value(attrv, attr_info["childs"]))

                ret_entry["attrs"].append(
                    {
                        "id": attrs[0].id,
                        "name": attrs[0].name,
                        "value": value,
                    }
                )

            return ret_entry

        request_data = {
            "schemas": ["LBVirtualServer"],
            "attrs": [
                {
                    "name": "LB",
                    "is_array": False,
                    "childs": [],
                },
                {
                    "name": "LBServiceGroup",
                    "is_array": True,
                    "childs": [
                        {
                            "name": "LBServer",
                            "is_array": True,
                            "childs": [
                                {
                                    "name": "IP Addresses",
                                    "is_array": False,
                                    "childs": [],
                                }
                            ],
                        }
                    ],
                },
                {
                    "name": "LBPolicyTemplate",
                    "is_array": True,
                    "childs": [
                        {
                            "name": "LBServiceGroup",
                            "is_array": True,
                            "childs": [
                                {
                                    "name": "LBServer",
                                    "is_array": True,
                                    "childs": [
                                        {
                                            "name": "IP Addresses",
                                            "is_array": False,
                                            "childs": [],
                                        }
                                    ],
                                }
                            ],
                        }
                    ],
                },
            ],
        }

        def _get_prefetch(attr_info, is_child: bool = False, is_array: bool = False):
            prefetchs = []
            prefetch = "referral__schema"
            if attr_info["is_array"]:
                prefetch = "data_array__" + prefetch

            prefetchs.append(prefetch)

            for child in attr_info["childs"]:
                prefetchs.append(_get_prefetch(child, True, attr_info["is_array"]))

            attrv_prefetch = Prefetch(
                "values",
                AttributeValue.objects.filter(is_latest=True).prefetch_related(*prefetchs),
            )

            lookup = "attrs"
            if is_child:
                lookup = "referral__" + lookup
                if is_array:
                    lookup = "data_array__" + lookup

            return Prefetch(
                lookup,
                Attribute.objects.filter(
                    schema__is_active=True, schema__name=attr_info["name"]
                ).prefetch_related(attrv_prefetch),
                attr_info["name"],
            )

        atts_prefetchs = []
        for attr_info in request_data["attrs"]:
            atts_prefetchs.append(_get_prefetch(attr_info))

        ret_data = []
        for entry in (
            Entry.objects.filter(schema__name__in=request_data["schemas"], is_active=True)
            .prefetch_related(*atts_prefetchs)
            .select_related("schema")
        )[0:2]:
            ret_data.append(_get_entry(entry, request_data["attrs"]))

        return Response(ret_data)
