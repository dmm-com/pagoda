from collections.abc import Iterator
from typing import Any

from django.test import SimpleTestCase
from django.urls import URLPattern, URLResolver, get_resolver
from pydantic import ValidationError as PydanticValidationError
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.viewsets import ViewSetMixin

from airone.lib.drf import custom_exception_handler, get_bound_parent
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


class GetBoundParentTest(SimpleTestCase):
    def test_returns_none_for_unbound_field(self):
        field: serializers.Field = serializers.CharField()

        self.assertIsNone(get_bound_parent(field))

    def test_returns_parent_serializer_once_bound(self):
        class SomeSerializer(serializers.Serializer):
            x = serializers.CharField()

        instance = SomeSerializer()

        self.assertIs(get_bound_parent(instance.fields["x"]), instance)


class PermissionClassGateTest(SimpleTestCase):
    """Guard the permission-class pattern behind past authorization findings.

    DRF never calls ``has_object_permission`` for collection actions such as
    ``create`` or for plain ``GenericAPIView`` handlers, so an authorization rule
    written only there is dead code. This test fails when such a class reaches a
    viewset, and when a known superuser gate stops being wired.
    """

    # Permission classes that intentionally implement only object level checks.
    # Each one is safe because the action that needs a collection level decision is
    # handled elsewhere; keep this list explicitly justified when extending it.
    ALLOWED_OBJECT_ONLY_PERMISSIONS = {
        # UserAPI.create is handled by UserCreateSerializer, which only lets a
        # non-superuser mint read-only co-users.
        "user.api_v2.views.UserPermission",
        # EntryAPI has no create route: entries are created through
        # EntityEntryAPI (EntityPermission.has_permission) and
        # EntryCreateSerializer.validate both require Writable on the schema.
        "entry.api_v2.views.EntryPermission",
        # ACLAPI only exposes retrieve/update.
        "acl.api_v2.views.ACLPermission",
    }

    # Views whose permission wiring is security critical. Removing the gate from any
    # of them would re-open a privilege escalation.
    EXPECTED_GATES = {
        "GroupAPI": {
            "create": "UserPermission",
            "update": "UserPermission",
            "destroy": "UserPermission",
        },
        "GroupImportAPI": {"post": "IsSuperuser"},
        "UserImportAPI": {"post": "IsSuperuser"},
        "RoleImportAPI": {"post": "IsSuperuser"},
    }

    def _iter_view_classes(self) -> Iterator[type[ViewSetMixin]]:
        def walk(patterns: list[URLPattern | URLResolver]) -> Iterator[type[ViewSetMixin]]:
            for pattern in patterns:
                if isinstance(pattern, URLResolver):
                    yield from walk(pattern.url_patterns)
                else:
                    view_class = getattr(pattern.callback, "cls", None)
                    # GenericViewSet is not a subclass of ViewSet; both derive
                    # from ViewSetMixin, so that is what we key on.
                    if view_class and issubclass(view_class, ViewSetMixin):
                        yield view_class

        yield from walk(get_resolver().url_patterns)

    def _permission_classes(self, permission: Any) -> Iterator[type[BasePermission]]:
        # `IsAuthenticated & Foo` is an OperandHolder, not a class.
        if hasattr(permission, "op1_class"):
            yield from self._permission_classes(permission.op1_class)
            yield from self._permission_classes(permission.op2_class)
        else:
            yield permission

    def test_no_object_only_permission_class_is_added(self) -> None:
        found: set[str] = set()
        for view_class in set(self._iter_view_classes()):
            for permission in view_class.permission_classes:
                for permission_class in self._permission_classes(permission):
                    # BasePermission.has_permission() always returns True, so a
                    # class that does not define its own has_permission decides
                    # nothing for collection actions such as create.
                    if "has_permission" not in permission_class.__dict__:
                        found.add(
                            "%s.%s" % (permission_class.__module__, permission_class.__name__)
                        )

        self.assertEqual(
            found,
            self.ALLOWED_OBJECT_ONLY_PERMISSIONS,
            "Object-only permission classes reached a ViewSet: %s" % sorted(found),
        )

    def test_privileged_views_keep_their_gates(self) -> None:
        for view_class in set(self._iter_view_classes()):
            expected = self.EXPECTED_GATES.get(view_class.__name__)
            if expected is None:
                continue

            names = {
                permission_class.__name__
                for permission in view_class.permission_classes
                for permission_class in self._permission_classes(permission)
            }
            self.assertTrue(
                set(expected.values()) <= names,
                "%s lost its permission gate (expected %s, got %s)"
                % (view_class.__name__, expected, names),
            )
