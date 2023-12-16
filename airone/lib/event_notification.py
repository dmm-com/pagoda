import json

import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning

from airone import settings
from airone.lib.log import Logger

urllib3.disable_warnings(InsecureRequestWarning)


def _send_request_to_webhook_endpoint(entry, user, event_type):
    if not settings.AIRONE_FLAGS["WEBHOOK"]:
        Logger.warning(
            "skipped to send requests to endpoints because webhook is disabled. skipped webhook urls are %s",
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


def notify_entry_create(entry, user):
    # send a request to the registered WebHook URL
    _send_request_to_webhook_endpoint(entry, user, "entry.create")


def notify_entry_update(entry, user):
    # send a request to the registered WebHook URL
    _send_request_to_webhook_endpoint(entry, user, "entry.update")


def notify_entry_delete(entry, user):
    # send a request to the registered WebHook URL
    _send_request_to_webhook_endpoint(entry, user, "entry.delete")
