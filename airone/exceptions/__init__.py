class AirOneBaseException(Exception):
    """The root of the exception class hierarchy for all server exceptions."""

    pass


class ElasticsearchException(AirOneBaseException):
    pass
