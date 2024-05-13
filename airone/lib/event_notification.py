import json
from typing import Literal

import requests
import urllib3
from django.conf import settings
from urllib3.exceptions import InsecureRequestWarning

from airone.lib.log import Logger
from entry.models import Entry
from user.models import User

urllib3.disable_warnings(InsecureRequestWarning)

EventType = Literal["entry.create", "entry.update", "entry.delete"]


def _send_request_to_webhook_endpoint(entry: Entry, user: User, event_type: EventType):
    if not settings.AIRONE_FLAGS["WEBHOOK"]:
        Logger.warning(
            "skipped to send requests because webhook is disabled. skipped urls are %s",
            [w.url for w in entry.schema.webhooks.filter(is_enabled=True, is_verified=True)],
        )
        return

    # send requests for each webhook endpoints
    for webhook in entry.schema.webhooks.filter(is_enabled=True, is_verified=True):
        requests.post(
            webhook.url,
            headers={x["header_key"]: x["header_value"] for x in webhook.headers},
            verify=False,
            data=json.dumps(
                {
                    "event": event_type,
                    "data": entry.to_dict(user),
                    "user": user.username,
                }
            ),
        )


def notify_entry_create(entry: Entry, user: User):
    # send a request to the registered WebHook URL
    _send_request_to_webhook_endpoint(entry, user, "entry.create")


def notify_entry_update(entry: Entry, user: User):
    # send a request to the registered WebHook URL
    _send_request_to_webhook_endpoint(entry, user, "entry.update")


def notify_entry_delete(entry: Entry, user: User):
    # send a request to the registered WebHook URL
    _send_request_to_webhook_endpoint(entry, user, "entry.delete")
