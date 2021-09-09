from django.db import models


class Webhook(models.Model):
    """
    This data-structure describes the feature to notify events (e.g. changing Entry)
    """
    # This describes what this webhook is for user
    label = models.TextField()

    # This describes URL endpoint which a notifying request will be sent
    url = models.URLField()

    # This is set by user when user want to enable for notifying events to the webhook_url
    is_enabled = models.BooleanField(default=False)

    # This is set by system when specified webhook_url is available
    is_verified = models.BooleanField(default=False)

    # This contains HTTP headers when sending request to the specified URL
    # (e.g. authentication header if it's needed)
    headers = models.TextField()

    def to_dict(self):
        return {
            'lebel': self.label,
            'url': self.url,
            'is_enabled': self.is_enabled,
            'is_verified': self.is_verified,
            'headers': self.headers,
        }
