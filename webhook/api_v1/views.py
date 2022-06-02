import json
import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning

from airone.lib.acl import ACLType
from airone.lib.http import get_obj_with_check_perm
from airone.lib.http import http_post

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.http import HttpResponse
from django.http.response import JsonResponse
from entity.models import Entity

from webhook.models import Webhook

urllib3.disable_warnings(InsecureRequestWarning)


@http_post(
    [
        {"name": "label", "type": str},
        {"name": "webhook_url", "type": str},
        {"name": "is_enabled", "type": bool},
        {"name": "request_headers", "type": list},
    ]
)
def set_webhook(request, entity_id, recv_data):
    entity, error = get_obj_with_check_perm(request.user, Entity, entity_id, ACLType.Full)
    if error:
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
        # get Webhook instance and set values
        webhook = Webhook.objects.filter(id=recv_data["id"]).first()
        if not webhook:
            return HttpResponse("Invalid Webhook ID is specified", status=400)

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

    resp = requests.post(
        recv_data["webhook_url"],
        **{
            "headers": {
                x["header_key"]: x["header_value"] for x in recv_data.get("request_headers", [])
            },
            "data": json.dumps({}),
            "verify": False,
        }
    )

    # The is_verified parameter will be set True,
    # when requests received HTTP 200 from specifying endpoint.
    webhook.is_verified = resp.ok
    webhook.save()

    return JsonResponse({"webhook_id": webhook.id, "msg": "Succeded in registering Webhook"})


# FIXME specify HTTP method
def del_webhook(request, webhook_id):
    webhook = Webhook.objects.filter(id=webhook_id).first()
    if not webhook:
        return HttpResponse("Specified webhook has already been deleted", status=400)

    # delete specified webhook
    webhook.delete()

    return HttpResponse("Succeded in deleting Webhook")
