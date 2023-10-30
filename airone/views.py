from django.shortcuts import redirect

from airone import settings


def index(request):
    if "LEGACY_UI_DISABLED" in settings.AIRONE and settings.AIRONE["LEGACY_UI_DISABLED"]:
        return redirect("ui/")
    return redirect("dashboard/")
