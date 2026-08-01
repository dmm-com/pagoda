import importlib
from dataclasses import dataclass, field
from typing import Any, Literal, Sequence

import tablib
from import_export.exceptions import ImportError as ImportExportError
from import_export.resources import ModelResource
from import_export.results import Result, RowResult

from acl.models import ACLBase
from airone.lib.acl import ACLType
from user.models import User

# Reasons why a row is not applied. They are reported to the user through the
# import preview so that silently-dropped rows become visible before importing.
SkipReason = Literal["spoofing", "permission_denied", "disallow_update"]

PreviewAction = Literal["create", "update", "unchanged", "skip", "error"]


@dataclass
class PreviewChange:
    """A single field-level difference that the import would apply."""

    field_name: str
    before: str | None
    after: str | None


@dataclass
class PreviewRow:
    """The outcome the import would produce for one row, without applying it."""

    action: PreviewAction
    name: str
    changes: list[PreviewChange] = field(default_factory=list)
    reason: str | None = None


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
    def preview_data_from_request(cls, data: dict[str, object], request_user: User) -> PreviewRow:
        """Report what importing ``data`` would do, without reporting errors as exceptions.

        This runs the very same import path as :meth:`import_data_from_request`, so the
        preview reflects every validation and permission rule the real import applies.
        It therefore *does* write to the database, and the caller MUST run it inside a
        transaction that is rolled back afterwards (see
        ``entity.api_v2.serializers.EntityImportExportRootSerializer.build_preview``).
        Running the real path rather than import-export's ``dry_run`` is deliberate:
        rows imported earlier in the same request (e.g. a new Entity) must be visible
        to rows imported later (e.g. an EntityAttr referring to it).
        """
        name = str(data.get("name", ""))

        try:
            resource, dataset = cls._build_resource_and_dataset(data, request_user)
        except RuntimeError as e:
            return PreviewRow(action="error", name=name, reason=str(e))

        # Snapshot the current values before importing. RowResult.original is a copy
        # made before the update, but its many-to-many managers resolve through the
        # database and would therefore report post-update values.
        before_values = resource.snapshot_comparing_values(dataset)

        try:
            result = resource.import_data(dataset, raise_errors=True)
        except ImportExportError as e:
            reason = str(e.error) if isinstance(e.error, Exception) else str(e)
            return PreviewRow(action="error", name=name, reason=reason)
        except Exception as e:
            # A preview must never fail the whole request; report the row as an error
            # so the user can see which row is problematic.
            return PreviewRow(action="error", name=name, reason=str(e))

        if not result.rows:
            return PreviewRow(action="error", name=name, reason="No row was processed")

        return resource.build_preview_row(result.rows[0], name, before_values)

    def snapshot_comparing_values(self, dataset: tablib.Dataset) -> dict[str, str | None] | None:
        """Return the current value of every COMPARING_KEYS field, or None if new."""
        try:
            instance_loader = self._meta.instance_loader_class(self, dataset)
            row = dict(zip(dataset.headers, dataset[0], strict=True))
            instance = self.get_instance(instance_loader, row)
        except Exception:
            # Identifying the existing instance is best-effort; import_data() below
            # reports the real error when the row cannot be processed at all.
            return None

        if instance is None:
            return None
        return {key: self._stringify(getattr(instance, key, None)) for key in self.COMPARING_KEYS}

    def build_preview_row(
        self,
        row_result: RowResult,
        name: str,
        before_values: dict[str, str | None] | None,
    ) -> PreviewRow:
        instance = row_result.instance

        match row_result.import_type:
            case RowResult.IMPORT_TYPE_NEW:
                return PreviewRow(
                    action="create",
                    name=name,
                    # Resources have to opt in to Meta.store_instance for a diff to be
                    # built. Without it the action alone is still worth reporting.
                    changes=self._build_changes(None, instance) if instance else [],
                )
            case RowResult.IMPORT_TYPE_SKIP:
                return PreviewRow(action="skip", name=name, reason=self.skip_reason)
            case RowResult.IMPORT_TYPE_UPDATE:
                if instance is None:
                    return PreviewRow(action="update", name=name)
                changes = self._build_changes(before_values, instance)
                # AironeModelResource.skip_row() intentionally does not skip unchanged
                # rows, so an "update" without any difference means nothing happens.
                if not changes:
                    return PreviewRow(action="unchanged", name=name)
                return PreviewRow(action="update", name=name, changes=changes)
            case _:
                errors = row_result.errors
                reason = str(errors[0].error) if errors else row_result.import_type
                return PreviewRow(action="error", name=name, reason=reason)

    def _build_changes(
        self, before_values: dict[str, str | None] | None, instance: Any
    ) -> list[PreviewChange]:
        changes: list[PreviewChange] = []
        for key in self.COMPARING_KEYS:
            after = self._stringify(getattr(instance, key, None))
            before = before_values.get(key) if before_values else None
            if before != after:
                changes.append(PreviewChange(field_name=key, before=before, after=after))
        return changes

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
