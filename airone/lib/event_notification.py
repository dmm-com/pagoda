import json
import requests


def _send_request_to_webhook_endpoint(entry, user, event_type):
    try:
        request_headers = json.loads(entry.schema.webhook_headers)
    except Exception:
        request_headers = {}

    payload = {
        'event': event_type,
        'data': entry.to_dict(user),
    }
    return requests.post(entry.schema.webhook_url,
                         data=json.dumps(payload),
                         headers=request_headers,
                         verify=False)


def notify_entry_create(entry, user):
    # complement attrs before sending request
    entry.complement_attrs(user)

    # send a request to the registered WebHook URL
    return _send_request_to_webhook_endpoint(entry, user, 'entry.create')


def notify_entry_update(entry, user):
    # complement attrs before sending request
    entry.complement_attrs(user)

    # send a request to the registered WebHook URL
    return _send_request_to_webhook_endpoint(entry, user, 'entry.update')


def notify_entry_delete(entry, user):
    # send a request to the registered WebHook URL
    return _send_request_to_webhook_endpoint(entry, user, 'entry.delete')
