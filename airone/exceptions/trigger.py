from rest_framework.exceptions import ValidationError
from airone.exceptions import AirOneBaseException


class InvalidInputException(ValidationError):
    default_code = "AE-300000"
