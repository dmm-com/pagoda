import json
from typing import Any, cast

import requests
import urllib3
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.http import HttpRequest, HttpResponse
from django.http.response import JsonResponse
from requests.exceptions import ConnectionError
from urllib3.exceptions import InsecureRequestWarning

from airone.lib.acl import ACLType
from airone.lib.http import get_obj_with_check_perm, http_post
from entity.models import Entity
from user.models import User
from webhook.models import Webhook

urllib3.disable_warnings(InsecureRequestWarning)


def _has_full_permission_on_webhook(user: User, webhook: Webhook) -> bool:
    """A webhook is shared with every entity that registers it, so the
    requester needs full control on all of them to modify or delete it."""
    entities = list(webhook.registered_entity.all())
    return bool(entities) and all(user.has_permission(entity, ACLType.Full) for entity in entities)


@http_post(
    [
        {"name": "label", "type": str},
        {"name": "webhook_url", "type": str},
        {"name": "is_enabled", "type": bool},
        {"name": "request_headers", "type": list},
    ]
)
def set_webhook(request: HttpRequest, entity_id: int, recv_data: dict[str, Any]) -> HttpResponse:
    user = cast(User, request.user)
    entity, error = get_obj_with_check_perm(
        user,
        Entity,
        entity_id,
        ACLType.Full,
    )
    if error or entity is None:
        assert error is not None
        return error

    if not entity.is_active:
        return JsonResponse({"msg": "There is no entity for setting"}, status=400)

    # check specified parameters are valid
    validate = URLValidator()
    try:
        # This checks webhook_url is valid HTTP URL
        validate(recv_data["webhook_url"])

    except ValidationError:
        return HttpResponse("Specified URL is invalid", status=400)

    if "id" in recv_data:
        # Only webhooks that are registered to the entity the caller is
        # authorized for can be updated. Looking the id up globally would let a
        # user hijack another entity's webhook (IDOR) and receive its events.
        try:
            webhook_id = int(recv_data["id"])
        except (TypeError, ValueError):
            return HttpResponse("Invalid Webhook ID is specified", status=400)

        webhook = entity.webhooks.filter(id=webhook_id).first()
        if not webhook:
            return HttpResponse("Invalid Webhook ID is specified", status=400)

        # The webhook may also be registered to other entities, which this
        # update would affect as well.
        if not _has_full_permission_on_webhook(user, webhook):
            return HttpResponse("You don't have permission to update this webhook", status=403)

        webhook.url = recv_data["webhook_url"]
        webhook.label = recv_data["label"]
        webhook.headers = recv_data.get("request_headers", [])
        webhook.is_enabled = recv_data["is_enabled"]
    else:
        # create Webhook instance and set values
        webhook = Webhook.objects.create(
            **{
                "url": recv_data["webhook_url"],
                "label": recv_data["label"],
                "headers": recv_data.get("request_headers", []),
                "is_enabled": recv_data["is_enabled"],
            }
        )
        entity.webhooks.add(webhook)

    try:
        resp = requests.post(
            recv_data["webhook_url"],
            headers={
                x["header_key"]: x["header_value"] for x in recv_data.get("request_headers", [])
            },
            data=json.dumps({}),
            verify=False,
        )

        # The is_verified parameter will be set True,
        # when requests received HTTP 200 from specifying endpoint.
        if resp.ok:
            webhook.is_verified = True
            webhook.verification_error_details = None
        else:
            webhook.is_verified = False
            webhook.verification_error_details = resp.reason
    except ConnectionError as e:
        webhook.is_verified = False
        webhook.verification_error_details = str(e)

    webhook.save()

    return JsonResponse({"webhook_id": webhook.id, "msg": "Succeded in registering Webhook"})


# The method and the authentication have to be checked here because this view
# is not wrapped by http_get/http_post helpers.
def del_webhook(request: HttpRequest, webhook_id: int) -> HttpResponse:
    if request.method != "DELETE":
        return HttpResponse("Invalid HTTP method is specified", status=400)

    if not request.user.is_authenticated:
        return HttpResponse("You have to login to execute this operation", status=401)

    webhook = Webhook.objects.filter(id=webhook_id).first()
    if not webhook:
        return HttpResponse("Specified webhook has already been deleted", status=400)

    # A webhook belongs to the entities it is registered to. Only a user who
    # has full control on all of them is allowed to delete it.
    if not _has_full_permission_on_webhook(request.user, webhook):
        return HttpResponse("You don't have permission to delete this webhook", status=403)

    # delete specified webhook
    webhook.delete()

    return HttpResponse("Succeded in deleting Webhook")
