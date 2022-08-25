import yaml
from django.conf import settings
from rest_framework.exceptions import ParseError, ValidationError
from rest_framework.parsers import BaseParser
from rest_framework.views import exception_handler


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


# error codes:
# https://github.com/dmm-com/airone/wiki/(Blueprint)-AirOne-API-Error-code-mapping


class DuplicatedObjectExistsError(ValidationError):

    def __init__(self, detail=None):
        super().__init__(detail, "AE-220000")  # duplicated object exists


def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    # Now add the HTTP status code to the response.
    if response is not None:
        for key in response.data.keys():
            for i, error in enumerate(response.data[key]):
                response.data[key][i] = {
                   'airone_error_code': error.code,
                   'detail': error,
                }

    return response
