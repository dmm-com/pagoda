from django.conf import settings
from django.conf.urls import include, url
from django.contrib.auth import views as auth_views

from airone import views
from airone.auth import view as auth_view
from api_v1.urls import urlpatterns as api_v1_urlpatterns

urlpatterns = [
    url(r"^$", views.index, name="index"),
    url(r"^testtest/", include(("acl.urls", "acl"))),
    url(r"^acl/", include(("acl.urls", "acl"))),
    url(r"^user/", include(("user.urls", "user"))),
    url(r"^group/", include(("group.urls", "group"))),
    url(r"^entity/", include(("entity.urls", "entity"))),
    url(r"^dashboard/", include(("dashboard.urls", "dashboard"))),
    url(r"^ui/", include(("dashboard.urls_for_ui", "dashboard_for_ui"))),
    url(r"^entry/", include(("entry.urls", "entry"))),
    url(r"^api/v1/", include(api_v1_urlpatterns)),
    url(r"^api/v2/", include(("api_v2.urls", "api_v2"))),
    url(r"^job/", include(("job.urls", "job"))),
    url(r"^auth/sso/", include("social_django.urls", namespace="social")),
    url(
        r"^auth/login/",
        auth_views.LoginView.as_view(
            redirect_authenticated_user=True,
            extra_context={
                "title": settings.AIRONE["TITLE"],
                "subtitle": settings.AIRONE["SUBTITLE"],
                "note_desc": settings.AIRONE["NOTE_DESC"],
                "note_link": settings.AIRONE["NOTE_LINK"],
                "sso_desc": settings.AIRONE["SSO_DESC"],
                "idp": list(settings.SOCIAL_AUTH_SAML_ENABLED_IDPS.keys())[0]
                if hasattr(settings, "SOCIAL_AUTH_SAML_ENABLED_IDPS")
                else None,
            },
        ),
        name="login",
    ),
    url(r"^auth/logout/", auth_view.logout, name="logout"),
    url(r"^webhook/", include(("webhook.urls", "webhook"))),
    url(r"^role/", include(("role.urls", "role"))),
]

if settings.DEBUG:
    urlpatterns.append(url(r"^__debug__/", include("debug_toolbar.urls")))

for extension in settings.AIRONE["EXTENSIONS"]:
    urlpatterns.append(
        url(r"^extension/%s" % extension, include(("%s.urls" % extension, extension)))
    )
