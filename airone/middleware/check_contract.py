import re

from django.conf import settings
from django.contrib.auth import logout
from django.http import HttpResponseRedirect


class CheckUserAgreement:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        print("[onix/CheckUserAgreement(00)]")
        if request.user.is_authenticated and settings.AIRONE.get("CHECK_USER_AGREEMENT"):
            print("[onix/CheckUserAgreement(01)] COOKIE: %s" % str(request.COOKIES))
            print("[onix/CheckUserAgreement(01)] AGREE_TERM_OF_SERVICE: %s" % str(request.COOKIES.get("AGREE_TERM_OF_SERVICE")))
            if request.COOKIES.get("AGREE_TERM_OF_SERVICE"):
                resp = self.get_response(request)
                resp.set_cookie("AGREE_TERM_OF_SERVICE", "YES")

                return resp
            else:
                logout(request)
                # return HttpResponseRedirect("/auth/logout")

        return self.get_response(request)
