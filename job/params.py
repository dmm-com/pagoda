"""Typed and fail-closed parameter contracts for core jobs.

The module deliberately does not import :mod:`job.models` at import time.  Job
creation uses these contracts from ``job.models``, so importing the enum here
would create a cycle.  Core operation ids are checked against the enum by
``assert_core_registry_complete`` and by the test suite.
"""

from __future__ import annotations

import json
from typing import Any, Generic, Literal, TypeAlias, TypeVar

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
    TypeAdapter,
    ValidationInfo,
    field_validator,
    model_validator,
)

from airone.lib.types import AttrType


class JobParamsModel(BaseModel):
    """Base contract for object-root job parameters."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True, validate_default=True)


RootValue = TypeVar("RootValue")


class JobParamsRootModel(RootModel[RootValue], Generic[RootValue]):
    """Base contract for non-object roots with the same strictness guarantees."""

    model_config = ConfigDict(strict=True, frozen=True, validate_default=True)


class EmptyParams(JobParamsModel):
    pass


class AttributeValue(JobParamsModel):
    """Attribute input whose value depends on its entity attribute definition."""

    id: int
    value: Any = None


class LegacyIndexedValue(JobParamsModel):
    data: Any = None
    index: int = 0

    @field_validator("index", mode="before")
    @classmethod
    def coerce_legacy_index(cls, value: Any) -> Any:
        if isinstance(value, str) and value.isdecimal():
            return int(value)
        return value


class LegacyCreateAttributeValue(JobParamsModel):
    id: str
    entity_attr_id: str | None = None
    type: str | int | None = None
    value: list[LegacyIndexedValue]
    referral_key: list[LegacyIndexedValue] = Field(default_factory=list)


class LegacyEditAttributeValue(LegacyCreateAttributeValue):
    entity_attr_id: str


class LegacyCreateEntryParams(JobParamsModel):
    entry_name: str
    attrs: list[LegacyCreateAttributeValue]


class LegacyEditEntryParams(JobParamsModel):
    entry_name: str
    attrs: list[LegacyEditAttributeValue]


class CopyEntryParams(JobParamsModel):
    new_name_list: list[str] = Field(default_factory=list)
    post_data: dict[str, Any] = Field(default_factory=dict)


class DoCopyEntryParams(JobParamsModel):
    new_name_list: list[str] = Field(default_factory=list)
    new_name: str
    post_data: dict[str, Any] = Field(default_factory=dict)


class ImportedAttribute(JobParamsModel):
    name: str
    value: Any = None


class ImportedEntry(JobParamsModel):
    id: int | None = None
    name: str
    attrs: list[ImportedAttribute] = Field(default_factory=list)


class LegacyImportedEntry(JobParamsModel):
    name: str
    attrs: dict[str, Any]


class LegacyImportEntryParams(JobParamsRootModel[list[LegacyImportedEntry]]):
    pass


class ImportEntryParams(JobParamsModel):
    entity: str
    entries: list[ImportedEntry] = Field(default_factory=list)
    # The approved-preview linkage recorded by EntryImportAPI. Optional so a
    # direct import (no preview) keeps the minimal shape.
    preview_job_id: int | None = None


class ExportEntryParams(JobParamsModel):
    export_format: Literal["yaml", "csv"]
    target_id: int
    join_attrs: list[dict[str, Any]] = Field(default_factory=list)

    @field_validator("target_id", mode="before")
    @classmethod
    def coerce_legacy_target_id(cls, value: Any) -> Any:
        if isinstance(value, str) and value.isdecimal():
            return int(value)
        return value


class AttrHintParams(JobParamsModel):
    name: str
    keyword: str | None = None
    filter_key: int | None = None
    exact_match: bool | None = None
    is_readable: bool | None = None


class JoinAttrParams(JobParamsModel):
    name: str
    offset: int = 0
    attrinfo: list[AttrHintParams] = Field(default_factory=list)


class SearchExportParams(JobParamsModel):
    entities: list[int]
    attrinfo: list[AttrHintParams]
    export_style: Literal["yaml", "csv"]
    has_referral: bool = False
    referral_name: str | None = None
    entry_name: str | None = None
    hint_entry: dict[str, Any] | None = None
    join_attrs: list[JoinAttrParams] = Field(default_factory=list)
    is_all_entities: bool = False

    @field_validator("entities", mode="before")
    @classmethod
    def coerce_legacy_entity_ids(cls, value: Any) -> Any:
        if isinstance(value, list):
            return [
                int(item) if isinstance(item, str) and item.isdecimal() else item for item in value
            ]
        return value


class ReferralParams(JobParamsModel):
    pass


class GroupReferralParams(JobParamsModel):
    group_id: int


class RoleReferralParams(JobParamsModel):
    role_id: int


class UpdateDocumentParams(JobParamsModel):
    is_update: bool = False


class EntityAttrParams(JobParamsModel):
    id: int | None = None
    name: str = Field(max_length=200)
    type: int
    is_mandatory: bool = False
    is_delete_in_chain: bool = False
    row_index: str = "0"
    ref_ids: list[int] = Field(default_factory=list)
    deleted: bool | None = None

    @field_validator("type", mode="before")
    @classmethod
    def coerce_legacy_type(cls, value: Any) -> Any:
        # HTML form submissions historically persisted AttrType as a decimal string.
        if isinstance(value, str) and value.isdecimal():
            return int(value)
        return value

    @field_validator("id", mode="before")
    @classmethod
    def coerce_legacy_id(cls, value: Any) -> Any:
        # HTML form submissions historically persisted ids as decimal strings.
        if isinstance(value, str) and value.isdecimal():
            return int(value)
        return value


class CreateEntityParams(JobParamsModel):
    name: str
    note: str
    is_toplevel: bool
    attrs: list[EntityAttrParams]


class EditEntityParams(JobParamsModel):
    name: str = Field(max_length=200)
    note: str
    is_toplevel: bool
    attrs: list[EntityAttrParams]


class WebhookHeaderParams(JobParamsModel):
    header_key: str
    header_value: str


class WebhookParams(JobParamsModel):
    id: int | None = None
    url: str = Field(default="", max_length=200)
    label: str = ""
    is_enabled: bool = False
    headers: list[WebhookHeaderParams] = Field(default_factory=list)
    is_deleted: bool = False


class EntityAttrV2Params(JobParamsModel):
    id: int | None = None
    name: str = Field(max_length=200)
    type: int
    index: int | None = None
    is_mandatory: bool = False
    is_delete_in_chain: bool = False
    is_summarized: bool = False
    referral: list[int] = Field(default_factory=list)
    note: str = ""
    default_value: str | bool | int | float | None = None
    choices: list[dict[str, str]] | None = None
    name_order: int | None = 0
    name_prefix: str | None = ""
    name_postfix: str | None = ""
    display_attr: str = ""
    deleted: bool | None = None
    is_deleted: bool = False
    created_user: Any = Field(default=None, exclude=True)

    @field_validator("referral", mode="before")
    @classmethod
    def coerce_serializer_referrals(cls, value: Any) -> Any:
        return _coerce_model_ids(value)

    @field_validator("choices", mode="after")
    @classmethod
    def validate_choices(cls, value: list[dict[str, str]] | None, info: ValidationInfo) -> Any:
        attr_type = info.data.get("type")
        if value is None:
            if attr_type in (AttrType.SELECT, AttrType.MULTI_SELECT):
                raise ValueError("SELECT type requires a non-empty choices list")
            return None
        if attr_type not in (AttrType.SELECT, AttrType.MULTI_SELECT):
            return None
        from entity.models import EntityAttr

        EntityAttr.validate_choices(value)
        return value

    @field_validator("default_value", mode="after")
    @classmethod
    def normalize_default_value(cls, value: Any, info: ValidationInfo) -> Any:
        return _normalize_entity_attr_default(value, info.data.get("type"))


class EditEntityAttrV2Params(JobParamsModel):
    id: int | None = None
    name: str | None = Field(default=None, max_length=200)
    type: int | None = None
    index: int | None = None
    is_mandatory: bool | None = None
    is_delete_in_chain: bool | None = None
    is_summarized: bool | None = None
    referral: list[int] | None = None
    note: str | None = None
    default_value: str | bool | int | float | None = None
    choices: list[dict[str, str]] | None = None
    is_deleted: bool = False
    name_order: int | None = 0
    name_prefix: str | None = ""
    name_postfix: str | None = ""
    display_attr: str | None = None
    created_user: Any = Field(default=None, exclude=True)

    @field_validator("referral", mode="before")
    @classmethod
    def coerce_serializer_referrals(cls, value: Any) -> Any:
        return _coerce_model_ids(value)

    @field_validator("choices", mode="after")
    @classmethod
    def validate_choices(cls, value: list[dict[str, str]] | None, info: ValidationInfo) -> Any:
        attr_type = info.data.get("type")
        if value is None:
            return None
        if attr_type is not None and attr_type not in (AttrType.SELECT, AttrType.MULTI_SELECT):
            return None
        from entity.models import EntityAttr

        EntityAttr.validate_choices(value)
        return value

    @field_validator("default_value", mode="after")
    @classmethod
    def normalize_default_value(cls, value: Any, info: ValidationInfo) -> Any:
        return _normalize_entity_attr_default(value, info.data.get("type"))

    @model_validator(mode="after")
    def require_new_attribute_fields(self) -> "EditEntityAttrV2Params":
        if self.id is None and (self.name is None or self.type is None):
            raise ValueError("name and type are required for new attribute creation")
        return self


def _normalize_entity_attr_default(value: Any, attr_type: Any) -> Any:
    """Preserve the established async EntityAttr default normalization contract."""

    if value is None or attr_type is None:
        return value
    if attr_type in (AttrType.STRING, AttrType.TEXT):
        return value if isinstance(value, str) else None
    if attr_type == AttrType.BOOLEAN:
        return value if isinstance(value, bool) else None
    if attr_type == AttrType.NUMBER:
        return value if isinstance(value, (int, float)) and not isinstance(value, bool) else None
    return None


def _coerce_model_ids(value: Any) -> Any:
    """Convert DRF related-model values to the ids persisted in a job payload."""

    if not isinstance(value, list):
        return value
    return [item.pk if isinstance(getattr(item, "pk", None), int) else item for item in value]


class EditWebhookParams(JobParamsModel):
    id: int | None = None
    url: str | None = Field(default=None, max_length=200)
    label: str = ""
    is_enabled: bool = False
    headers: list[WebhookHeaderParams] = Field(default_factory=list)
    is_deleted: bool = False


class IsolationConditionParams(JobParamsModel):
    attr_id: int
    str_cond: str = ""
    ref_cond_id: int | None = None
    bool_cond: bool = False
    is_unmatch: bool = False


class IsolationActionParams(JobParamsModel):
    is_prevent_all: bool = False
    prevent_from_id: int | None = None


class IsolationRuleParams(JobParamsModel):
    id: int | None = None
    is_deleted: bool = False
    conditions: list[IsolationConditionParams] = Field(default_factory=list)
    action: IsolationActionParams = Field(default_factory=IsolationActionParams)


class CreateEntityV2Params(JobParamsModel):
    name: str = Field(max_length=200)
    note: str = ""
    item_name_pattern: str = ""
    item_name_type: str = ""
    is_toplevel: bool = False
    attrs: list[EntityAttrV2Params] = Field(default_factory=list)
    webhooks: list[WebhookParams] = Field(default_factory=list)
    isolation_rules: list[IsolationRuleParams] = Field(default_factory=list)
    delete_chain_exclude_entities: list[int] = Field(default_factory=list)


class EditEntityV2Params(JobParamsModel):
    id: int | None = None
    name: str | None = Field(default=None, max_length=200)
    note: str | None = None
    item_name_pattern: str | None = None
    item_name_type: str | None = None
    is_toplevel: bool | None = None
    attrs: list[EditEntityAttrV2Params] = Field(default_factory=list)
    webhooks: list[EditWebhookParams] = Field(default_factory=list)
    isolation_rules: list[IsolationRuleParams] = Field(default_factory=list)
    delete_chain_exclude_entities: list[int] = Field(default_factory=list)


class EntryV2Params(JobParamsModel):
    schema_id: int | None = Field(default=None, alias="schema")
    entity: int | str | None = None
    name: str | None = None
    attrs: list[AttributeValue] = Field(default_factory=list)
    delay_trigger: bool = True
    call_stacks: list[int] = Field(default_factory=list)


class CreateEntryV2Params(EntryV2Params):
    name: str

    @model_validator(mode="after")
    def require_entity_schema(self) -> "CreateEntryV2Params":
        if self.schema_id is None and self.entity is None:
            raise ValueError("schema is required")
        return self


class RoleImportItem(JobParamsModel):
    id: int | None = None
    name: str
    description: str = ""
    users: list[str] = Field(default_factory=list)
    groups: list[str] = Field(default_factory=list)
    admin_users: list[str] = Field(default_factory=list)
    admin_groups: list[str] = Field(default_factory=list)
    permissions: list[dict[str, Any]] = Field(default_factory=list)


class RoleImportParams(JobParamsRootModel[list[RoleImportItem]]):
    pass


class TriggerListParams(
    JobParamsRootModel[list[LegacyCreateAttributeValue | LegacyEditAttributeValue | AttributeValue]]
):
    pass


class BulkEditParams(JobParamsModel):
    modelid: int
    attrinfo: list[AttrHintParams] = Field(default_factory=list)
    hint_entry: dict[str, Any] | None = None
    referral_name: str | None = None
    value: AttributeValue


class EntityImportItem(JobParamsModel):
    id: int | None = None
    name: str | None = None
    note: str | None = None
    item_name_pattern: str | None = None
    status: int | None = None
    created_user: str | None = None


class EntityAttrImportItem(JobParamsModel):
    id: int | None = None
    name: str | None = None
    type: int | None = None
    entity: str | None = None
    is_mandatory: bool | Literal["0", "1"] = False
    created_user: str | None = None
    refer: str


class ImportEntityPreviewParams(JobParamsModel):
    Entity: list[EntityImportItem]
    EntityAttr: list[EntityAttrImportItem]


ParamsContract: TypeAlias = type[BaseModel]


# Keep the ids literal here to preserve the no-import-cycle property.  The
# exhaustiveness assertion below makes any JobOperation addition fail closed.
def _build_core_registry(entries: list[tuple[int, ParamsContract]]) -> dict[int, ParamsContract]:
    registry = dict(entries)
    if len(registry) != len(entries):
        raise RuntimeError("Duplicate core job parameter operation id")
    return registry


CORE_JOB_PARAMS: dict[int, ParamsContract] = _build_core_registry(
    [
        (1, LegacyCreateEntryParams),
        (2, LegacyEditEntryParams),
        (3, EmptyParams),
        (4, CopyEntryParams),
        (5, LegacyImportEntryParams),
        (6, ExportEntryParams),
        (7, EmptyParams),
        (8, SearchExportParams),
        (9, ReferralParams),
        (10, CreateEntityParams),
        (11, EditEntityParams),
        (12, EmptyParams),
        (13, EmptyParams),
        (14, EmptyParams),
        (15, EmptyParams),
        (16, DoCopyEntryParams),
        (17, ImportEntryParams),
        (18, GroupReferralParams),
        (19, RoleReferralParams),
        (20, ExportEntryParams),
        (21, UpdateDocumentParams),
        (22, SearchExportParams),
        (23, TriggerListParams),
        (24, CreateEntityV2Params),
        (25, EditEntityV2Params),
        (26, EmptyParams),
        (27, CreateEntryV2Params),
        (28, EntryV2Params),
        (29, EmptyParams),
        (30, RoleImportParams),
        (31, BulkEditParams),
        (32, ImportEntityPreviewParams),
        # Same payload shape as IMPORT_ENTRY_V2 (and the optional approved-preview
        # linkage, which an import job carries but a preview job never sets).
        (33, ImportEntryParams),
    ]
)

_custom_job_params: dict[int, ParamsContract] = {}


def register_job_params(operation: int, contract: ParamsContract) -> None:
    """Register a parameter contract for a custom/plugin operation."""

    operation_id = int(operation)
    if not isinstance(contract, type) or not issubclass(contract, BaseModel):
        raise TypeError("Job parameter contract must be a Pydantic model class")
    if operation_id in CORE_JOB_PARAMS:
        raise ValueError(f"Cannot replace core job parameter contract for operation {operation_id}")
    if operation_id in _custom_job_params:
        raise ValueError(
            f"Job parameter contract for operation {operation_id} is already registered"
        )
    _custom_job_params[operation_id] = contract


def unregister_job_params(operation: int) -> None:
    """Remove a custom contract, primarily for plugin teardown and isolated tests."""

    _custom_job_params.pop(int(operation), None)


def get_job_params_contract(operation: int) -> ParamsContract:
    operation_id = int(operation)
    if operation_id in CORE_JOB_PARAMS:
        return CORE_JOB_PARAMS[operation_id]
    try:
        return _custom_job_params[operation_id]
    except KeyError:
        raise ValueError(f"No job parameter contract for operation {operation_id}") from None


def validate_job_params(operation: int, params: Any) -> Any:
    """Validate Python input and return a Pydantic model (or union member)."""

    return TypeAdapter(get_job_params_contract(operation)).validate_python(params)


def parse_job_params(operation: int, params_json: str | bytes | bytearray) -> Any:
    """Validate JSON persisted in ``Job.params``."""

    # Some historical MAY_INVOKE_TRIGGER jobs stored the old default ``{}``.
    # Keep that read compatibility isolated from validation of newly created jobs.
    if int(operation) == 23:
        encoded = params_json.encode() if isinstance(params_json, str) else bytes(params_json)
        if encoded.strip() == b"{}":
            return TriggerListParams([])
    return TypeAdapter(get_job_params_contract(operation)).validate_json(params_json)


def serialize_job_params(operation: int, params: Any) -> str:
    """Validate and emit deterministic JSON-mode storage representation."""

    contract = TypeAdapter(get_job_params_contract(operation))
    validated = contract.validate_python(params)
    json_value = contract.dump_python(validated, mode="json", exclude_unset=True, by_alias=True)
    return json.dumps(json_value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def assert_core_registry_complete() -> None:
    """Fail when the enum and contract registry diverge."""

    # Local import is intentional; importing job.models at module load creates a cycle.
    from job.models import JobOperation

    operation_ids = {int(operation) for operation in JobOperation}
    registered_ids = set(CORE_JOB_PARAMS)
    if operation_ids != registered_ids:
        missing = sorted(operation_ids - registered_ids)
        unknown = sorted(registered_ids - operation_ids)
        raise RuntimeError(
            f"Incomplete core job params registry: missing={missing}, unknown={unknown}"
        )
