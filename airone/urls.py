from django.conf import settings
from django.contrib.auth import views as auth_views
<<<<<<< HEAD
from django.urls import include, re_path
from django.views.generic import RedirectView
=======
>>>>>>> master

from airone import views
from airone.auth import view as auth_view
from api_v1.urls import urlpatterns as api_v1_urlpatterns

urlpatterns = [
    re_path(r"^$", views.index, name="index"),
    re_path(r"^acl/", include(("acl.urls", "acl"))),
    re_path(r"^user/", include(("user.urls", "user"))),
    re_path(r"^group/", include(("group.urls", "group"))),
    re_path(r"^entity/", include(("entity.urls", "entity"))),
    re_path(r"^dashboard/", include(("dashboard.urls", "dashboard"))),
    re_path(r"^ui/", include(("dashboard.urls_for_ui", "dashboard_for_ui"))),
    re_path(r"^entry/", include(("entry.urls", "entry"))),
    re_path(r"^api/v1/", include(api_v1_urlpatterns)),
    re_path(r"^api/v2/", include(("api_v2.urls", "api_v2"))),
    re_path(r"^job/", include(("job.urls", "job"))),
    re_path(r"^auth/sso/", include("social_django.urls", namespace="social")),
    re_path(
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
    re_path(r"^auth/logout/", auth_view.logout, name="logout"),
    re_path(r"^webhook/", include(("webhook.urls", "webhook"))),
    re_path(r"^role/", include(("role.urls", "role"))),
]

if settings.DEBUG:
    urlpatterns.append(re_path(r"^__debug__/", include("debug_toolbar.urls")))

for extension in settings.AIRONE["EXTENSIONS"]:
    urlpatterns.append(
        re_path(r"^extension/%s" % extension, include(("%s.urls" % extension, extension)))
    )
