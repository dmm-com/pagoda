# Copyright (c) Django Software Foundation and individual contributors.
# All rights reserved.
#
# It partially reuses the original implementation at django.contrib.auth.forms.PasswordResetForm
# with supporting username based email resolution.
#

from django import forms
from django.contrib.auth.forms import UserModel, UsernameField
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMultiAlternatives
from django.template import loader
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


class UsernameBasedPasswordResetForm(forms.Form):
    """
    A customized PasswordResetForm to send only an email relating to a given username.
    """

    username = UsernameField(max_length=254)

    USERNAME_FIELD = UserModel.USERNAME_FIELD
    EMAIL_FIELD = UserModel.get_email_field_name()

    def send_mail(
        self,
        subject_template_name,
        email_template_name,
        context,
        from_email,
        to_email,
        html_email_template_name=None,
    ):
        """
        Sends a django.core.mail.EmailMultiAlternatives to `to_email`.
        """
        subject = loader.render_to_string(subject_template_name, context)
        # Email subject *must not* contain newlines
        subject = "".join(subject.splitlines())
        body = loader.render_to_string(email_template_name, context)

        email_message = EmailMultiAlternatives(subject, body, from_email, [to_email])
        if html_email_template_name is not None:
            html_email = loader.render_to_string(html_email_template_name, context)
            email_message.attach_alternative(html_email, "text/html")

        email_message.send()

    def get_user(self, username):
        """
        Given a username, return matching user who should receive a reset or None.
        """
        active_users = UserModel._default_manager.filter(
            **{
                "%s__iexact" % self.USERNAME_FIELD: username,
                "is_active": True,
            }
        )
        if len(active_users) == 1 and active_users[0].has_usable_password():
            return active_users[0]
        else:
            return None

    def save(
        self,
        domain_override=None,
        subject_template_name="registration/password_reset_subject.txt",
        email_template_name="registration/password_reset_email.html",
        use_https=False,
        token_generator=default_token_generator,
        from_email=None,
        request=None,
        html_email_template_name=None,
        extra_email_context=None,
    ):
        """
        Generates a one-use only link for resetting password and sends to the
        user.
        """
        username = self.cleaned_data["username"]
        user = self.get_user(username)
        if user:
            if not domain_override:
                current_site = get_current_site(request)
                site_name = current_site.name
                domain = current_site.domain
            else:
                site_name = domain = domain_override
            user_email = getattr(user, self.EMAIL_FIELD)
            context = {
                "email": user_email,
                "domain": domain,
                "site_name": site_name,
                "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                "user": user,
                "token": token_generator.make_token(user),
                "protocol": "https" if use_https else "http",
            }
            if extra_email_context is not None:
                context.update(extra_email_context)
            self.send_mail(
                subject_template_name,
                email_template_name,
                context,
                from_email,
                user_email,
                html_email_template_name=html_email_template_name,
            )
