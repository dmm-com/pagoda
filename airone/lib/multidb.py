from typing import Any, Callable

from django.http import HttpRequest, HttpResponse
from multidb.middleware import PinningRouterMiddleware
from multidb.pinning import unpin_this_thread

ViewT = Any  # may be a function, a DRF view class, or a DRF view_func with .cls


def db_readonly(view: ViewT) -> ViewT:
    """Mark a view as read-only at the DB layer.

    Counterpart to ``multidb.pinning.db_write``. Overrides the
    HTTP-method-based heuristic in ``PinningRouterMiddleware`` that would
    otherwise pin a non-safe-method (POST/PUT/PATCH/DELETE) request, and the
    next ``MULTIDB_PINNING_SECONDS`` seconds of reads from the same client,
    to the primary DB.

    Use this for views that must accept a non-safe HTTP method for payload
    size reasons (e.g. the advanced-search APIs that ship complex filters in
    the request body) but do not perform any DB writes.
    """
    view._db_readonly = True
    return view


def _view_opts_in_to_replica(view_func: Callable[..., Any]) -> bool:
    cls = getattr(view_func, "cls", None)
    if cls is not None and getattr(cls, "_db_readonly", False):
        return True
    return bool(getattr(view_func, "_db_readonly", False))


class AironePinningRouterMiddleware(PinningRouterMiddleware):  # type: ignore[misc]
    """Pagoda-flavored PinningRouterMiddleware.

    Honors the ``@db_readonly`` marker on a resolved view by undoing the
    parent middleware's master-pin and skipping the ``MULTIDB_PINNING_COOKIE``
    so that the request reads from a replica and subsequent reads from the
    same client are not forced to the primary.
    """

    def process_view(
        self,
        request: HttpRequest,
        view_func: Callable[..., Any],
        view_args: list[Any],
        view_kwargs: dict[str, Any],
    ) -> None:
        if _view_opts_in_to_replica(view_func):
            unpin_this_thread()
            request._airone_db_readonly = True  # type: ignore[attr-defined]

    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        if getattr(request, "_airone_db_readonly", False) and not getattr(
            response, "_db_write", False
        ):
            return response
        result: HttpResponse = super().process_response(request, response)
        return result
