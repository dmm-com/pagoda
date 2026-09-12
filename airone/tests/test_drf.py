from django.test import SimpleTestCase
from pydantic import ValidationError as PydanticValidationError
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from airone.lib.drf import custom_exception_handler
from job.params import EntityAttrV2Params, ExportEntryParams


class PydanticValidationErrorHandlerTest(SimpleTestCase):
    def _handle_pydantic(self, payload: dict) -> Response:
        with self.assertRaises(PydanticValidationError) as context:
            ExportEntryParams.model_validate(payload)
        response = custom_exception_handler(context.exception, {})
        assert response is not None
        return response

    def test_incorrect_type_is_a_400_with_ae_121000(self):
        response = self._handle_pydantic({"export_format": "yaml", "target_id": True})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["target_id"][0]["code"], "AE-121000")

    def test_missing_field_is_a_400_with_ae_113000(self):
        response = self._handle_pydantic({})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["export_format"][0]["code"], "AE-113000")
        self.assertEqual(response.data["target_id"][0]["code"], "AE-113000")

    def test_extra_field_reports_its_location(self):
        response = self._handle_pydantic(
            {"export_format": "yaml", "target_id": 1, "unexpected": "x"}
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["unexpected"][0]["code"], "AE-121000")

    def test_nested_field_location_is_preserved(self):
        with self.assertRaises(PydanticValidationError) as context:
            EntityAttrV2Params.model_validate({"name": "attr", "type": 1, "referral": ["x"]})
        response = custom_exception_handler(context.exception, {})

        assert response is not None
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["referral.0"][0]["code"], "AE-121000")

    def test_plain_drf_validation_error_still_maps(self):
        response = custom_exception_handler(ValidationError("plain error"), {})

        assert response is not None
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data[0]["code"], "AE-121000")
