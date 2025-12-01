from typing import Optional

from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

from airone.celery import app
from airone.lib import custom_view
from airone.lib.job import may_schedule_until_job_is_ready, register_job_task
from airone.lib.log import Logger
from airone.lib.types import AttrType
from entity.api_v2.serializers import EntityCreateSerializer, EntityUpdateSerializer
from entity.models import Entity, EntityAttr
from job.models import Job, JobOperation, JobStatus
from user.models import History, User

# ============================================================================
# Pydantic Models for Job Parameters
# ============================================================================


class CreateEntityAttr(BaseModel):
    """Attribute definition for CREATE_ENTITY (V1) task."""

    name: str = Field(..., max_length=200)
    type: int
    is_mandatory: bool
    is_delete_in_chain: bool
    row_index: str
    ref_ids: list[int] = Field(default_factory=list)

    @field_validator("type", mode="before")
    @classmethod
    def validate_type(cls, v):
        """Convert string type to int if needed."""
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError:
                raise ValueError(f"Invalid type value: {v}")
        return v


class CreateEntityParams(BaseModel):
    """Parameters for CREATE_ENTITY (V1) task."""

    attrs: list[CreateEntityAttr]


class EditEntityAttr(BaseModel):
    """Attribute definition for EDIT_ENTITY (V1) task."""

    id: Optional[int] = None
    name: str = Field(..., max_length=200)
    type: int
    is_mandatory: bool
    is_delete_in_chain: bool
    row_index: str
    ref_ids: list[int] = Field(default_factory=list)
    deleted: Optional[bool] = None

    @field_validator("type", mode="before")
    @classmethod
    def validate_type(cls, v):
        """Convert string type to int if needed."""
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError:
                raise ValueError(f"Invalid type value: {v}")
        return v


class EditEntityParams(BaseModel):
    """Parameters for EDIT_ENTITY (V1) task."""

    name: str = Field(..., max_length=200)
    note: str
    attrs: list[EditEntityAttr]


class WebhookHeader(BaseModel):
    """Webhook HTTP header definition."""

    header_key: str
    header_value: str


class CreateEntityV2Webhook(BaseModel):
    """Webhook definition for CREATE_ENTITY_V2 task."""

    url: str = Field(default="", max_length=200)
    label: str = ""
    is_enabled: bool = False
    headers: list[WebhookHeader] = Field(default_factory=list)


class CreateEntityV2Attr(BaseModel):
    """Attribute definition for CREATE_ENTITY_V2 task."""

    name: str = Field(..., max_length=200)
    type: int
    index: Optional[int] = None
    is_mandatory: bool = False
    is_delete_in_chain: bool = False
    is_summarized: bool = False
    referral: list[int] = Field(default_factory=list)
    note: str = ""
    default_value: Optional[str | bool | int | float] = None

    @model_validator(mode="after")
    def validate_default_value_for_type(self):
        """Validate that default_value is compatible with the attribute type."""
        if self.default_value is None:
            return self

        supported_types = [AttrType.STRING, AttrType.TEXT, AttrType.BOOLEAN, AttrType.NUMBER]

        # Clear default_value for unsupported types (don't raise error)
        if self.type not in supported_types:
            Logger.warning(
                f"default_value is not supported for type {self.type}. "
                f"Clearing default_value. Supported types: {supported_types}"
            )
            self.default_value = None
            return self

        # Type-specific validation - clear if invalid type
        is_valid = True
        if self.type in [AttrType.STRING, AttrType.TEXT]:
            if not isinstance(self.default_value, str):
                is_valid = False
        elif self.type == AttrType.BOOLEAN:
            if not isinstance(self.default_value, bool):
                is_valid = False
        elif self.type == AttrType.NUMBER:
            if not isinstance(self.default_value, (int, float)):
                is_valid = False

        if not is_valid:
            Logger.warning(
                f"default_value type mismatch for attribute type {self.type}. "
                f"Clearing default_value. Got: {type(self.default_value)}"
            )
            self.default_value = None

        return self


class CreateEntityV2Params(BaseModel):
    """Parameters for CREATE_ENTITY_V2 task."""

    name: str = Field(..., max_length=200)
    note: str = ""
    item_name_pattern: str = ""
    is_toplevel: bool = False
    attrs: list[CreateEntityV2Attr] = Field(default_factory=list)
    webhooks: list[CreateEntityV2Webhook] = Field(default_factory=list)


class EditEntityV2Webhook(BaseModel):
    """Webhook definition for EDIT_ENTITY_V2 task."""

    id: Optional[int] = None
    url: Optional[str] = Field(None, max_length=200)
    label: str = ""
    is_enabled: bool = False
    headers: list[WebhookHeader] = Field(default_factory=list)
    is_deleted: bool = False


class EditEntityV2Attr(BaseModel):
    """Attribute definition for EDIT_ENTITY_V2 task."""

    id: Optional[int] = None
    name: Optional[str] = Field(None, max_length=200)
    type: Optional[int] = None
    index: Optional[int] = None
    is_mandatory: Optional[bool] = None
    is_delete_in_chain: Optional[bool] = None
    is_summarized: Optional[bool] = None
    referral: Optional[list[int]] = None
    note: Optional[str] = None
    default_value: Optional[str | bool | int | float] = None
    is_deleted: bool = False

    @model_validator(mode="after")
    def validate_attr_fields(self):
        """Validate that required fields are present based on operation type."""
        if self.id is None:
            if self.name is None or self.type is None:
                raise ValueError("name and type are required for new attribute creation")
        return self

    @model_validator(mode="after")
    def validate_default_value_for_type(self):
        """Validate default_value compatibility with attribute type."""
        if self.default_value is None or self.type is None:
            return self

        supported_types = [AttrType.STRING, AttrType.TEXT, AttrType.BOOLEAN, AttrType.NUMBER]

        # Clear default_value for unsupported types (don't raise error)
        if self.type not in supported_types:
            Logger.warning(
                f"default_value is not supported for type {self.type}. "
                f"Clearing default_value. Supported types: {supported_types}"
            )
            self.default_value = None
            return self

        # Type-specific validation - clear if invalid type
        is_valid = True
        if self.type in [AttrType.STRING, AttrType.TEXT]:
            if not isinstance(self.default_value, str):
                is_valid = False
        elif self.type == AttrType.BOOLEAN:
            if not isinstance(self.default_value, bool):
                is_valid = False
        elif self.type == AttrType.NUMBER:
            if not isinstance(self.default_value, (int, float)):
                is_valid = False

        if not is_valid:
            Logger.warning(
                f"default_value type mismatch for attribute type {self.type}. "
                f"Clearing default_value. Got: {type(self.default_value)}"
            )
            self.default_value = None

        return self


class EditEntityV2Params(BaseModel):
    """Parameters for EDIT_ENTITY_V2 task."""

    id: Optional[int] = None
    name: Optional[str] = Field(None, max_length=200)
    note: Optional[str] = None
    item_name_pattern: Optional[str] = None
    is_toplevel: Optional[bool] = None
    attrs: list[EditEntityV2Attr] = Field(default_factory=list)
    webhooks: list[EditEntityV2Webhook] = Field(default_factory=list)


# ============================================================================
# Task Functions
# ============================================================================


@register_job_task(JobOperation.CREATE_ENTITY)
@app.task(bind=True)
@may_schedule_until_job_is_ready
def create_entity(self, job: Job) -> JobStatus:
    user = User.objects.filter(id=job.user.id).first()
    entity = Entity.objects.filter(id=job.target.id, is_active=True).first()

    if not entity or not user:
        # Abort when specified entity doesn't exist
        return JobStatus.CANCELED

    # for history record
    entity._history_user = user

    # Validate and parse job parameters using Pydantic
    try:
        params = CreateEntityParams.model_validate_json(job.params)
    except ValidationError as e:
        Logger.error(f"Invalid parameters for CREATE_ENTITY job {job.id}: {e}")
        return JobStatus.ERROR

    # register history to modify Entity
    history = user.seth_entity_add(entity)

    for attr in params.attrs:
        attr_base = EntityAttr.objects.create(
            name=attr.name,
            type=attr.type,
            is_mandatory=attr.is_mandatory,
            is_delete_in_chain=attr.is_delete_in_chain,
            created_user=user,
            parent_entity=entity,
            index=int(attr.row_index),
        )

        if attr.type & AttrType.OBJECT:
            [attr_base.referral.add(Entity.objects.get(id=x)) for x in attr.ref_ids]

        # register history to modify Entity
        history.add_attr(attr_base)

    # clear flag to specify this entity has been completed to create
    entity.del_status(Entity.STATUS_CREATING)

    # update job status and save it
    return JobStatus.DONE


@register_job_task(JobOperation.EDIT_ENTITY)
@app.task(bind=True)
@may_schedule_until_job_is_ready
def edit_entity(self, job: Job) -> JobStatus:
    user = User.objects.filter(id=job.user.id).first()
    entity = Entity.objects.filter(id=job.target.id, is_active=True).first()

    if not entity or not user:
        # Abort when specified entity doesn't exist
        return JobStatus.CANCELED

    # for history record
    entity._history_user = user

    # Validate and parse job parameters using Pydantic
    try:
        params = EditEntityParams.model_validate_json(job.params)
    except ValidationError as e:
        Logger.error(f"Invalid parameters for EDIT_ENTITY job {job.id}: {e}")
        return JobStatus.ERROR

    # register history to modify Entity
    history = user.seth_entity_mod(entity)
    if entity.name != params.name:
        history.mod_entity(entity, 'old name: "%s"' % (entity.name))

    if entity.name != params.name:
        entity.name = params.name
        entity.save(update_fields=["name"])

    if entity.note != params.note:
        entity.note = params.note
        entity.save(update_fields=["note"])

    # update processing for each attrs
    deleted_attr_ids = []
    for attr in params.attrs:
        if attr.deleted:
            # In case of deleting attribute which has been already existed
            attr_obj = EntityAttr.objects.get(id=attr.id)
            attr_obj.delete()

            # Save deleted EntityAttr id to update es_document of Entries
            # that are refered by associated AttributeValues.
            deleted_attr_ids.append(attr_obj.id)

            # register History to register deleting EntityAttr
            history.del_attr(attr_obj)

        elif attr.id is not None and EntityAttr.objects.filter(id=attr.id).exists():
            # In case of updating attribute which has been already existed
            attr_obj = EntityAttr.objects.get(id=attr.id)

            # register operaion history if the parameters are changed
            if attr_obj.name != attr.name:
                history.mod_attr(attr_obj, 'old name: "%s"' % (attr_obj.name))

            if attr_obj.is_mandatory != attr.is_mandatory:
                if attr.is_mandatory:
                    history.mod_attr(attr_obj, "set mandatory flag")
                else:
                    history.mod_attr(attr_obj, "unset mandatory flag")

            # EntityAttr.is_referral_updated() is separated from EntityAttr.is_updated()
            # to reduce unnecessary creation of HistoricalRecord.
            update_params = {
                "name": attr.name,
                "index": attr.row_index,
                "is_mandatory": attr.is_mandatory,
                "is_delete_in_chain": attr.is_delete_in_chain,
            }
            if attr_obj.is_updated(**update_params):
                attr_obj.name = attr.name
                attr_obj.is_mandatory = attr.is_mandatory
                attr_obj.is_delete_in_chain = attr.is_delete_in_chain
                attr_obj.index = int(attr.row_index)

                attr_obj.save()

            if (attr_obj.type & AttrType.OBJECT) and (attr_obj.is_referral_updated(attr.ref_ids)):
                # the case of an attribute that has referral entry
                attr_obj.referral_clear()
                attr_obj.referral.add(*[Entity.objects.get(id=x) for x in attr.ref_ids])

        else:
            # In case of creating new attribute
            attr_obj = EntityAttr.objects.create(
                name=attr.name,
                type=attr.type,
                is_mandatory=attr.is_mandatory,
                is_delete_in_chain=attr.is_delete_in_chain,
                index=int(attr.row_index),
                created_user=user,
                parent_entity=entity,
            )

            # append referral objects
            if attr.type & AttrType.OBJECT:
                [attr_obj.referral.add(Entity.objects.get(id=x)) for x in attr.ref_ids]

            # register History to register adding EntityAttr
            history.add_attr(attr_obj)

    # clear flag to specify this entity has been completed to edit
    entity.del_status(Entity.STATUS_EDITING)

    # update job status and save it
    return JobStatus.DONE


@register_job_task(JobOperation.DELETE_ENTITY)
@app.task(bind=True)
@may_schedule_until_job_is_ready
def delete_entity(self, job: Job) -> JobStatus:
    user = User.objects.filter(id=job.user.id).first()
    entity = Entity.objects.filter(id=job.target.id, is_active=False).first()

    if not entity or not user:
        # Abort when specified entity doesn't exist
        return JobStatus.CANCELED

    # for history record
    entity._history_user = user

    entity.delete()

    history = user.seth_entity_del(entity)

    # Delete all attributes which target Entity have
    for attr in entity.attrs.all():
        attr.delete()
        history.del_attr(attr)

    return JobStatus.DONE


@register_job_task(JobOperation.CREATE_ENTITY_V2)
@app.task(bind=True)
@may_schedule_until_job_is_ready
def create_entity_v2(self, job: Job) -> JobStatus:
    entity: Entity | None = Entity.objects.filter(id=job.target.id, is_active=True).first()
    if not entity:
        return JobStatus.ERROR

    # Validate and parse job parameters using Pydantic
    try:
        params = CreateEntityV2Params.model_validate_json(job.params)
    except ValidationError as e:
        Logger.error(f"Invalid parameters for CREATE_ENTITY_V2 job {job.id}: {e}")
        return JobStatus.ERROR

    # Convert Pydantic model to dict for serializer
    # (EntityCreateSerializer expects dict input)
    # Use exclude_none=True to avoid passing None values that may violate DB constraints
    params_dict = params.model_dump(exclude_none=True)

    # pass to validate the params because the entity should be already created
    serializer = EntityCreateSerializer(data=params_dict, context={"_user": job.user})
    serializer.create_remaining(entity, serializer.initial_data)

    # update job status and save it
    return JobStatus.DONE


@register_job_task(JobOperation.EDIT_ENTITY_V2)
@app.task(bind=True)
@may_schedule_until_job_is_ready
def edit_entity_v2(self, job: Job) -> JobStatus:
    entity: Entity | None = Entity.objects.filter(id=job.target.id, is_active=True).first()
    if not entity:
        return JobStatus.ERROR

    # Validate and parse job parameters using Pydantic
    try:
        params = EditEntityV2Params.model_validate_json(job.params)
    except ValidationError as e:
        Logger.error(f"Invalid parameters for EDIT_ENTITY_V2 job {job.id}: {e}")
        return JobStatus.ERROR

    # Convert Pydantic model to dict for serializer
    # (EntityUpdateSerializer expects dict input)
    params_dict = params.model_dump(exclude_none=True)

    serializer = EntityUpdateSerializer(
        instance=entity, data=params_dict, context={"_user": job.user}
    )
    if not serializer.is_valid():
        return JobStatus.ERROR

    serializer.update_remaining(entity, serializer.validated_data)

    return JobStatus.DONE


@register_job_task(JobOperation.DELETE_ENTITY_V2)
@app.task(bind=True)
@may_schedule_until_job_is_ready
def delete_entity_v2(self, job: Job) -> JobStatus:
    entity: Entity | None = Entity.objects.filter(id=job.target.id, is_active=True).first()
    if not entity:
        return JobStatus.ERROR

    if custom_view.is_custom("before_delete_entity_v2"):
        custom_view.call_custom("before_delete_entity_v2", None, job.user, entity)

    # register operation History for deleting entity
    history: History = job.user.seth_entity_del(entity)
    entity.delete()

    # Delete all attributes which target Entity have
    entity_attr: EntityAttr
    for entity_attr in entity.attrs.filter(is_active=True):
        history.del_attr(entity_attr)
        entity_attr.delete()

    if custom_view.is_custom("after_delete_entity_v2"):
        custom_view.call_custom("after_delete_entity_v2", None, job.user, entity)

    return JobStatus.DONE
