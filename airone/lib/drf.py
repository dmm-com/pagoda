from collections import OrderedDict

import yaml
from django.conf import settings
from rest_framework import serializers
from rest_framework.exceptions import APIException, ParseError, ValidationError
from rest_framework.parsers import BaseParser
from rest_framework.renderers import BaseRenderer
from rest_framework.utils.serializer_helpers import ReturnDict, ReturnList
from rest_framework.views import exception_handler
from yaml import SafeDumper

from airone.lib.log import Logger

SafeDumper.add_representer(OrderedDict, yaml.representer.SafeRepresenter.represent_dict)
SafeDumper.add_representer(ReturnDict, yaml.representer.SafeRepresenter.represent_dict)
SafeDumper.add_representer(ReturnList, yaml.representer.SafeRepresenter.represent_list)


class YAMLParser(BaseParser):
    """
    Parses JSON-serialized data.
    """

    media_type = "application/yaml"

    def parse(self, stream, media_type=None, parser_context=None):
        """
        Parses the incoming bytestream as YAML and returns the resulting data.
        """
        parser_context = parser_context or {}
        encoding = parser_context.get("encoding", settings.DEFAULT_CHARSET)

        try:
            data = stream.read().decode(encoding)
            return yaml.safe_load(data)
        except (ValueError, yaml.parser.ParserError, yaml.scanner.ScannerError) as exc:
            raise ParseError("YAML parse error - %s" % str(exc))


class YAMLRenderer(BaseRenderer):
    """
    Renders JSON-serialized data.
    """

    media_type = "application/yaml"
    format = "yaml"
    charset = "utf-8"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        return yaml.dump(
            data, Dumper=SafeDumper, stream=None, default_flow_style=False, allow_unicode=True
        )


# error codes:
# https://github.com/dmm-com/airone/wiki/(Blueprint)-AirOne-API-Error-code-mapping


class RequiredParameterError(ValidationError):
    default_code = "AE-113000"


class IncorrectTypeError(ValidationError):
    default_code = "AE-121000"


class ExceedLimitError(ValidationError):
    default_code = "AE-122000"


class DuplicatedObjectExistsError(ValidationError):
    default_code = "AE-220000"


class ObjectNotExistsError(ValidationError):
    default_code = "AE-230000"


class EntryIsNotEmptyError(ValidationError):
    default_code = "AE-240000"


class InvalidValueError(ValidationError):
    default_code = "AE-250000"


class FrequentImportError(ValidationError):
    default_code = "AE-260000"


class JobIsNotDoneError(ValidationError):
    default_code = "AE-270000"


class FileIsNotExistsError(ValidationError):
    default_code = "AE-280000"


def custom_exception_handler(exc, context):
    def _convert_error_code(detail):
        if isinstance(detail, list):
            return [_convert_error_code(item) for item in detail]

        if "code" not in detail:
            return {key: _convert_error_code(value) for key, value in detail.items()}

        if "AE-" in detail["code"]:
            return detail

        error_code = {
            # "django or drf error_code": "airone error_code"
            "authentication_failed": "AE-000000",
            "not_authenticated": "AE-000000",
            "unsupported_media_type": "AE-130000",
            "parse_error": "AE-140000",
            "required": "AE-113000",
            "invalid": "AE-121000",
            "incorrect_type": "AE-121000",
            "not_a_list": "AE-121000",
            "max_value": "AE-122000",
            "max_length": "AE-122000",
            "empty": "AE-123000",
            "permission_denied": "AE-210000",
            "does_not_exist": "AE-230000",
            "not_found": "AE-230000",
        }

        # Convert Django, DRF error codes to for AirOne
        airone_error_code = error_code.get(detail["code"])
        if not airone_error_code:
            airone_error_code = "AE-999999"  # unknown error
            Logger.warning("unknown error(%s) has occurred" % detail)

        detail["code"] = airone_error_code
        return detail

    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    if response is not None:
        if isinstance(exc, APIException):
            response.data = exc.get_full_details()
        else:
            response.data = {
                "message": response.data["detail"],
                "code": response.data["detail"].code,
            }

        response.data = _convert_error_code(response.data)

    return response


class AironeUserDefault(serializers.CurrentUserDefault):
    """
    It enables to get user from the custom field in the context.
    The original CurrentUserDefault fetches it from request context,
    so it fails if the context doesn't have request.
    """

    def __call__(self, serializer_field):
        if "_user" in serializer_field.context:
            return serializer_field.context["_user"]

        return super().__call__(serializer_field)
