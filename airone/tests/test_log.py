from django.core import mail
from django.test import RequestFactory
from mock import Mock

from airone.middleware.log import LoggingRequestMiddleware
from airone.lib.test import AironeViewTest


class AirOneLogTest(AironeViewTest):
    def test_logging_request_middleware(self):
        user = self.guest_login()
        request = RequestFactory().get("/test/")
        request.user = user

        for status_code, level in [(200, "INFO"), (400, "WARNING"), (500, "ERROR")]:

            def get_response(request):
                return Mock(status_code=status_code)

            with self.assertLogs("airone") as log:
                middleware = LoggingRequestMiddleware(get_response)
                middleware(request)

            self.assertEqual(len(log.output), 1)
            self.assertRegex(
                log.output[0],
                r"%s:airone:\(Profiling result: 0.[0-9]+s\) \(user-id: %s\) GET /test/ %s$"
                % (level, user.id, status_code),
            )

    def test_logging_request_middleware_without_user(self):
        request = RequestFactory().get("/test/")

        def get_response(request):
            return Mock(status_code=200)

        with self.assertLogs("airone") as log:
            middleware = LoggingRequestMiddleware(get_response)
            middleware(request)

        self.assertEqual(len(log.output), 1)
        self.assertRegex(
            log.output[0],
            r"%s:airone:\(Profiling result: 0.[0-9]+s\) \(user-id: %s\) GET /test/ %s$"
            % ("INFO", None, 200),
        )

    def test_logging_request_middleware_with_exception(self):
        user = self.guest_login()
        path = "/test/"
        request = RequestFactory().get(path)
        request.user = user
        exception = Mock(side_effect=Exception("MockException"))
        admins = [("admin", "airone@example.com")]

        with self.settings(ADMINS=admins, EMAIL_SUBJECT_PREFIX=""):
            middleware = LoggingRequestMiddleware(Mock())
            resp = middleware.process_exception(request, exception)

            self.assertEqual(len(mail.outbox), 1)
            self.assertEqual(mail.outbox[0].to, [a[1] for a in admins])
            self.assertEqual(mail.outbox[0].subject, "ERROR Django Request %s" % path)
            self.assertEqual(resp.status_code, 500)
            self.assertEqual(resp.content.decode("utf-8"), "Internal Server Error")
