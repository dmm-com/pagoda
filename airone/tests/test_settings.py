from unittest import mock

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from airone import settings as settings_module
from airone.settings import Dev, Prd
from airone.settings_common import DEFAULT_SECRET_KEY, ensure_secure_secret_key


class EnsureSecureSecretKeyTest(SimpleTestCase):
    def test_missing_key_is_rejected(self):
        with self.assertRaises(ImproperlyConfigured):
            ensure_secure_secret_key(None)

    def test_empty_key_is_rejected(self):
        with self.assertRaises(ImproperlyConfigured):
            ensure_secure_secret_key("")

    def test_default_key_is_rejected(self):
        with self.assertRaises(ImproperlyConfigured):
            ensure_secure_secret_key(DEFAULT_SECRET_KEY)

    def test_former_helm_default_key_is_rejected(self):
        with self.assertRaises(ImproperlyConfigured):
            ensure_secure_secret_key("changeme")

    def test_generated_key_is_accepted(self):
        # No exception means the value is considered safe for production.
        ensure_secure_secret_key("k3y-generated-by-get_random_secret_key-0123456789")


class PrdSecretKeyStartupTest(SimpleTestCase):
    """Prd must stop booting, while Dev and lite mode keep running."""

    def _setup_prd(self, secret_key, lite=False):
        with (
            mock.patch.object(settings_module, "LITE", lite),
            mock.patch.object(Prd, "SECRET_KEY", secret_key),
        ):
            Prd.setup()

    def test_startup_fails_when_key_is_unset(self):
        # Without AIRONE_SECRET_KEY, the published fallback is used.
        with self.assertRaises(ImproperlyConfigured):
            self._setup_prd(DEFAULT_SECRET_KEY)

    def test_startup_fails_with_published_default_key(self):
        with self.assertRaises(ImproperlyConfigured):
            self._setup_prd("changeme")

    def test_startup_succeeds_with_proper_key(self):
        self._setup_prd("k3y-generated-by-get_random_secret_key-0123456789")

    def test_startup_succeeds_in_lite_mode(self):
        self._setup_prd(DEFAULT_SECRET_KEY, lite=True)

    def test_dev_startup_still_works_with_fallback_key(self):
        with mock.patch.object(Dev, "SECRET_KEY", DEFAULT_SECRET_KEY):
            Dev.setup()
