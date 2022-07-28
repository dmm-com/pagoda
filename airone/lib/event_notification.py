import json

import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning

urllib3.disable_warnings(InsecureRequestWarning)


def _send_request_to_webhook_endpoint(entry, user, event_type):
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
    # complement attrs before sending request
    entry.complement_attrs(user)

    # send a request to the registered WebHook URL
    _send_request_to_webhook_endpoint(entry, user, "entry.create")


def notify_entry_update(entry, user):
    # complement attrs before sending request
    entry.complement_attrs(user)

    # send a request to the registered WebHook URL
    _send_request_to_webhook_endpoint(entry, user, "entry.update")


def notify_entry_delete(entry, user):
    # send a request to the registered WebHook URL
    _send_request_to_webhook_endpoint(entry, user, "entry.delete")
