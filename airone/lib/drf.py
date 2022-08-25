import yaml
from django.conf import settings
from rest_framework.exceptions import ParseError
from rest_framework.parsers import BaseParser


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
