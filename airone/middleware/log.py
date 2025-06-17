import traceback
from time import time
from typing import Callable, Optional

from django.conf import settings
from django.core.mail import mail_admins
from django.http import HttpRequest, HttpResponse, HttpResponseServerError

from airone.lib.log import Logger


class LoggingRequestMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        start_time = time()

        response = self.get_response(request)

        user_id = request.user.id if hasattr(request, "user") else None
        logger_msg = "(Profiling result: %fs) (user-id: %s) %s %s %s" % (
            time() - start_time,
            user_id,
            request.method,
            request.path,
            response.status_code,
        )
        if response.status_code >= 500:
            Logger.error(logger_msg)
        elif response.status_code >= 400:
            Logger.warning(logger_msg)
        else:
            Logger.info(logger_msg)

        return response

    def process_exception(
        self, request: HttpRequest, exception: Exception
    ) -> Optional[HttpResponse]:
        traceback_msg = traceback.format_exc()
        subject = "ERROR Django Request " + request.path
        message = """
Request Method: {request.method}
Request URL: {request.path}
USER: {request.user.id}

raised exception:
{exception}

full traceback:
{traceback_msg}
""".format(request=request, exception=exception, traceback_msg=traceback_msg)

        # Print for DEBUG because email is not sent in dev environment
        print(message)

        # Send an email so that admins can receive errors
        mail_admins(subject, message)
        if not settings.DEBUG:
            return HttpResponseServerError("Internal Server Error")
        return None
