class AirOneBaseException(Exception):
    """The root of the exception class hierarchy for all server exceptions."""

    pass


class ElasticsearchException(AirOneBaseException):
    pass


class ImportDataError(AirOneBaseException):
    """The content of an import file cannot be applied (e.g. it names a missing record)."""
