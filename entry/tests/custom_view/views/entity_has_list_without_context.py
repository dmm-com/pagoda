from airone.lib.http import render
from django.http import HttpResponse


def list_entry_without_context(request, entity):
    return HttpResponse("return no data") if request.GET.get("return_resp", None) else None


def list_entry(request, entity, context):
    return render(request, "list_entry.html", dict(context, **{"test_key": "test_value"}))
