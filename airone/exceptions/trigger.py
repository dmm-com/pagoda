from rest_framework.exceptions import ValidationError


class InvalidInputException(ValidationError):
    default_code = "AE-300000"
