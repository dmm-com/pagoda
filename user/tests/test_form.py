from unittest import mock

from django.test import TestCase
from django.contrib.auth import hashers
from django.contrib.auth.models import User

from user.forms import UsernameBasedPasswordResetForm


class FormTest(TestCase):
    USERNAME = "form_test"
    PASSWORD = "dummy"
    EMAIL = "form_test@example.com"
    FROM_EMAIL = "airone@example.com"

    def test_get_user(self):
        User.objects.create(
            username=self.USERNAME,
            password=hashers.make_password(self.PASSWORD),
            email=self.EMAIL,
            is_active=True,
        )
        form = UsernameBasedPasswordResetForm()

        # An existing user
        user = form.get_user(self.USERNAME)
        self.assertEqual(getattr(user, User.USERNAME_FIELD), self.USERNAME)
        self.assertEqual(getattr(user, User.EMAIL_FIELD), self.EMAIL)

        # An unknown user
        unknown = form.get_user("unknown")
        self.assertIsNone(unknown)

    def test_save(self):
        User.objects.create(
            username=self.USERNAME,
            password=hashers.make_password(self.PASSWORD),
            email=self.EMAIL,
            is_active=True,
        )

        # An existing user
        with mock.patch("user.forms.UsernameBasedPasswordResetForm.send_mail") as m:
            form = UsernameBasedPasswordResetForm()
            form.cleaned_data = {"username": self.USERNAME}
            form.save(domain_override="example.com", from_email=self.FROM_EMAIL)
            self.assertTrue(m.called)
            args, kwargs = m.call_args
            self.assertEqual(args[3], self.FROM_EMAIL)  # from_email
            self.assertEqual(args[4], self.EMAIL)  # user_email

        # An unknown user
        with mock.patch("user.forms.UsernameBasedPasswordResetForm.send_mail") as m:
            form = UsernameBasedPasswordResetForm()
            form.cleaned_data = {"username": "unknown"}
            form.save(domain_override="example.com", from_email=self.FROM_EMAIL)
            self.assertFalse(m.called)
