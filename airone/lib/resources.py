import importlib
from typing import Any, Literal, Sequence

import tablib
from import_export.exceptions import ImportError as ImportExportError
from import_export.resources import ModelResource
from import_export.results import Result

from acl.models import ACLBase
from airone.lib.acl import ACLType
from user.models import User

# Reasons why a row is not applied. They are reported to the user through the
# import preview so that silently-dropped rows become visible before importing.
SkipReason = Literal["spoofing", "permission_denied", "disallow_update"]


class AironeModelResource(ModelResource):  # type: ignore[misc]
    COMPARING_KEYS: list[str] = []
    DISALLOW_UPDATE_KEYS: list[str] = []

    def __init__(self, *args: object, **kwargs: object) -> None:
        super(AironeModelResource, self).__init__(*args, **kwargs)

        # This parameter is needed to check that imported object has permission
        # to add/update it by the user who import data.
        self.request_user: User | None = None

        # Records why the last row was skipped. skip_row() only returns a boolean,
        # so this keeps the reason available for the import preview.
        self.skip_reason: SkipReason | None = None

    """
    This private method checks that two instance has same content in each attribute.
    """

    def _is_updated(self, comp1: ACLBase, comp2: ACLBase) -> bool:
        return bool(any([getattr(comp1, x) != getattr(comp2, x) for x in self.COMPARING_KEYS]))

    def validate_update(self, new: ACLBase, old: ACLBase) -> bool:
        # This cancels update when the value of disallow update key is updated.
        if not all([getattr(new, x) == getattr(old, x) for x in self.DISALLOW_UPDATE_KEYS]):
            return False
        return True

    def skip_row(
        self,
        instance: ACLBase,
        original: ACLBase,
        row: dict[str, object],
        import_validation_errors: dict[str, list[object]] | None = None,
    ) -> bool:
        self.skip_reason = None

        # the case of creating new instance
        if not self._meta.model.objects.filter(id=instance.id).exists():
            # Inhibits the spoofing
            if isinstance(instance, ACLBase) and instance.created_user != self.request_user:
                self.skip_reason = "spoofing"
                return True

        # the case of instance is updated
        elif self._is_updated(instance, original):
            # the case user try to update but he doen't have writable permition
            if not self.request_user or not self.request_user.has_permission(
                instance, ACLType.Writable
            ):
                self.skip_reason = "permission_denied"
                return True

            # the case user try to change params which are disallow to update
            if not self.validate_update(instance, original):
                self.skip_reason = "disallow_update"
                return True

        return False

    # event handler at calling after completion of import processing
    @classmethod
    def after_import_completion(cls, results: Sequence[Result]) -> None:
        pass

    @classmethod
    def normalize_import_row(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Shape a row the way the importer sees it: every header key, blank if absent."""
        return {key: data.get(key, "") or "" for key in cls._IMPORT_INFO["header"]}

    @classmethod
    def validate_import_row(cls, data: dict[str, object]) -> None:
        """Reject a row the import could not accept. Raises RuntimeError.

        The import preview calls this too, so that a row rejected here is
        reported the same way whether the user previews or imports.
        """
        # check mandatory keys are existed, or not
        if not all([x in data for x in cls._IMPORT_INFO["mandatory_keys"]]):
            raise RuntimeError("Mandatory key doesn't exist")

        # check that mandatory values is set
        if "mandatory_values" in cls._IMPORT_INFO and any(
            not data[x] for x in cls._IMPORT_INFO["mandatory_values"]
        ):
            raise RuntimeError(
                "The value of '%s' is needed" % str(cls._IMPORT_INFO["mandatory_values"])
            )

        # check unnecessary parameters are specified, or not
        if not all([x in cls._IMPORT_INFO["header"] for x in data.keys()]):
            raise RuntimeError("Unnecessary key is specified")

    @classmethod
    def _build_resource_and_dataset(
        cls, data: dict[str, object], request_user: User
    ) -> tuple["AironeModelResource", tablib.Dataset]:
        resource = getattr(
            importlib.import_module(cls._IMPORT_INFO["resource_module"]),
            cls._IMPORT_INFO["resource_model_name"],
        )()
        if not resource:
            raise RuntimeError("Resource object is not defined")

        # set user who import the data for checking permission
        resource.request_user = request_user

        cls.validate_import_row(data)

        # get dataset to import
        dataset = tablib.Dataset(
            [x in data and data[x] or "" for x in cls._IMPORT_INFO["header"]],
            headers=cls._IMPORT_INFO["header"],
        )

        return resource, dataset

    @classmethod
    def import_data_from_request(cls, data: dict[str, object], request_user: User) -> Result:
        resource, dataset = cls._build_resource_and_dataset(data, request_user)

        try:
            return resource.import_data(dataset, raise_errors=True)
        except ImportExportError as e:
            if isinstance(e.error, Exception):
                raise e.error from e
            raise

    @classmethod
    def _stringify(cls, value: Any) -> str | None:
        if value is None:
            return None
        # ManyToMany fields are exposed as a manager; render them as a sorted name list
        # so that the preview can diff them as plain text.
        if hasattr(value, "all"):
            return ",".join(sorted(cls._stringify_one(x) for x in value.all()))
        return cls._stringify_one(value)

    @staticmethod
    def _stringify_one(value: Any) -> str:
        # Related models are shown by name; ACLBase has no __str__ and would otherwise
        # render as "ACLBase object (1001)", which is meaningless in a diff.
        for attribute in ("name", "username"):
            label = getattr(value, attribute, None)
            if isinstance(label, str):
                return label
        return str(value)
