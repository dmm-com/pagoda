import json
from typing import Any, Optional, Protocol

from google.cloud import spanner_v1
from google.cloud.spanner_v1.database import Database
from google.cloud.spanner_v1.instance import Instance
from pydantic import BaseModel, Field

from airone.lib.elasticsearch import (
    AdvancedSearchResultRecord,
    AttrHint,
    FilterKey,
)
from airone.lib.types import AttrType
from entity.models import EntityAttr
from entry.api_v2.serializers import AdvancedSearchJoinAttrInfo
from entry.models import AttributeValue


class SpannerOperation(Protocol):
    """Protocol for Spanner operations (batch and mutation groups)"""

    def insert(
        self,
        table: str,
        columns: tuple[str, ...],
        values: list[tuple[Any, ...]],
    ) -> None: ...

    def delete(
        self,
        table: str,
        keyset: spanner_v1.KeySet,
    ) -> None: ...


class AdvancedSearchEntry(BaseModel):
    """Represents an entry in the advanced search system"""

    entry_id: str = Field(description="UUID of the entry")
    name: str = Field(max_length=200, description="Name of the entry")
    origin_entity_id: int = Field(description="Original entity ID from Django")
    origin_entry_id: int = Field(description="Original entry ID from Django")


class AdvancedSearchAttribute(BaseModel):
    """Represents an attribute in the advanced search system"""

    entry_id: str = Field(description="UUID of the parent entry")
    attribute_id: str = Field(description="UUID of the attribute")
    type: AttrType = Field(description="Type of the attribute")
    name: str = Field(max_length=200, description="Name of the attribute")
    origin_entity_attr_id: int = Field(description="Original entity attribute ID from Django")
    origin_attribute_id: int = Field(description="Original attribute ID from Django")


class AdvancedSearchAttributeValue(BaseModel):
    """Represents an attribute value in the advanced search system"""

    entry_id: str = Field(description="UUID of the parent entry")
    attribute_id: str = Field(description="UUID of the parent attribute")
    attribute_value_id: str = Field(description="UUID of the attribute value")
    value: str = Field(description="Searchable text value")
    raw_value: Optional[dict[str, Any] | list[Any]] = Field(description="JSON value data")

    @classmethod
    def create_instance(
        cls,
        entry_id: str,
        attribute_id: str,
        attribute_value_id: str,
        entity_attr: EntityAttr,
        attrv: AttributeValue | None,
    ) -> "AdvancedSearchAttributeValue":
        """Create an instance based on EntityAttr and AttributeValue.
        This follows the same conversion logic as AdvancedSearchAttributeIndex.
        """
        value: str | None = None
        raw_value: dict[str, Any] | list[Any] | None = None

        if attrv:
            match entity_attr.type:
                case AttrType.STRING | AttrType.TEXT:
                    value = attrv.value
                case AttrType.BOOLEAN:
                    value = "true" if attrv.boolean else "false"
                case AttrType.DATE:
                    value = attrv.date.isoformat() if attrv.date else None
                case AttrType.DATETIME:
                    value = attrv.datetime.isoformat() if attrv.datetime else None
                case AttrType.OBJECT:
                    value = attrv.referral.name if attrv.referral else None
                    raw_value = (
                        {"id": attrv.referral.id, "name": attrv.referral.name}
                        if attrv.referral
                        else None
                    )
                case AttrType.NAMED_OBJECT:
                    value = attrv.referral.name if attrv.referral else None
                    raw_value = {
                        str(attrv.value): {
                            "id": attrv.referral.id,
                            "name": attrv.referral.name,
                        }
                        if attrv.referral
                        else None
                    }
                case AttrType.GROUP:
                    value = attrv.group.name if attrv.group else None
                    raw_value = (
                        {"id": attrv.group.id, "name": attrv.group.name} if attrv.group else None
                    )
                case AttrType.ROLE:
                    value = attrv.role.name if attrv.role else None
                    raw_value = (
                        {"id": attrv.role.id, "name": attrv.role.name} if attrv.role else None
                    )
                case AttrType.ARRAY_STRING:
                    raw_value = [v.value for v in attrv.data_array.all()]
                    value = ",".join(raw_value)
                case AttrType.ARRAY_OBJECT:
                    raw_value = [
                        {"id": v.referral.id, "name": v.referral.name}
                        for v in attrv.data_array.all()
                        if v.referral
                    ]
                    value = ",".join([v["name"] for v in raw_value])
                case AttrType.ARRAY_NAMED_OBJECT:
                    raw_value = [
                        {v.value: {"id": v.referral.id, "name": v.referral.name}}
                        for v in attrv.data_array.all()
                        if v.referral
                    ]
                    value = ",".join(
                        [v.referral.name for v in attrv.data_array.all() if v.referral]
                    )
                case AttrType.ARRAY_GROUP:
                    raw_value = [
                        {"id": v.group.id, "name": v.group.name}
                        for v in attrv.data_array.all()
                        if v.group
                    ]
                    value = ",".join([v["name"] for v in raw_value])
                case AttrType.ARRAY_ROLE:
                    raw_value = [
                        {"id": v.role.id, "name": v.role.name}
                        for v in attrv.data_array.all()
                        if v.role
                    ]
                    value = ",".join([v["name"] for v in raw_value])
                case _:
                    print("TODO implement it")

        return cls(
            entry_id=entry_id,
            attribute_id=attribute_id,
            attribute_value_id=attribute_value_id,
            value=value or "",
            raw_value=raw_value,
        )


# Repository interface
class SpannerRepository:
    """Repository for interacting with Cloud Spanner"""

    def __init__(self, project_id: str, instance_id: str, database_id: str):
        self.client: spanner_v1.Client = spanner_v1.Client(project=project_id)
        self.instance: Instance = self.client.instance(instance_id)
        self.database: Database = self.instance.database(database_id)

    def insert_entries(
        self, entries: list[AdvancedSearchEntry], operation: SpannerOperation
    ) -> None:
        """Insert multiple entries in a batch or mutation group"""
        if not entries:
            return

        operation.insert(
            table="AdvancedSearchEntry",
            columns=("EntryId", "Name", "OriginEntityId", "OriginEntryId"),
            values=[
                (entry.entry_id, entry.name, entry.origin_entity_id, entry.origin_entry_id)
                for entry in entries
            ],
        )

    def insert_attributes(
        self, attrs: list[AdvancedSearchAttribute], operation: SpannerOperation
    ) -> None:
        """Insert multiple attributes in a batch or mutation group"""
        if not attrs:
            return

        operation.insert(
            table="AdvancedSearchAttribute",
            columns=(
                "EntryId",
                "AttributeId",
                "Type",
                "Name",
                "OriginEntityAttrId",
                "OriginAttributeId",
            ),
            values=[
                (
                    attr.entry_id,
                    attr.attribute_id,
                    attr.type.value,
                    attr.name,
                    attr.origin_entity_attr_id,
                    attr.origin_attribute_id,
                )
                for attr in attrs
            ],
        )

    def insert_attribute_values(
        self, values: list[AdvancedSearchAttributeValue], operation: SpannerOperation
    ) -> None:
        """Insert multiple attribute values in a batch or mutation group"""
        if not values:
            return

        operation.insert(
            table="AdvancedSearchAttributeValue",
            columns=("EntryId", "AttributeId", "AttributeValueId", "Value", "RawValue"),
            values=[
                (
                    value.entry_id,
                    value.attribute_id,
                    value.attribute_value_id,
                    value.value,
                    json.dumps(value.raw_value) if value.raw_value is not None else None,
                )
                for value in values
            ],
        )

    def insert_entry_referrals(
        self, entry_referrals: list[tuple[str, str, str]], operation: SpannerOperation
    ) -> None:
        """Insert entry referrals in a batch or mutation group.

        Args:
            entry_referrals: List of tuples (spanner_entry_id, spanner_attr_id, referral_entry_id)
            operation: Spanner operation (batch or mutation group)
        """
        if not entry_referrals:
            return

        # Insert the referral relationships
        operation.insert(
            table="AdvancedSearchEntryReferral",
            columns=("EntryId", "AttributeId", "ReferralId"),
            values=entry_referrals,
        )

    # Keep the single-record methods for backward compatibility
    def insert_entry(self, entry: AdvancedSearchEntry, transaction=None) -> None:
        """Insert a single entry"""
        self.insert_entries([entry], transaction)

    def insert_attribute(self, attr: AdvancedSearchAttribute, transaction=None) -> None:
        """Insert a single attribute"""
        self.insert_attributes([attr], transaction)

    def insert_attribute_value(self, value: AdvancedSearchAttributeValue, transaction=None) -> None:
        """Insert a single attribute value"""
        self.insert_attribute_values([value], transaction)

    def delete_entries_by_entity(self, entity_id: int, operation: SpannerOperation) -> None:
        """Delete all entries for a given entity"""
        # First get all entry IDs for the entity
        with self.database.snapshot() as snapshot:
            query = """
            SELECT EntryId FROM AdvancedSearchEntry
            WHERE OriginEntityId = @entity_id
            """
            results = snapshot.execute_sql(
                query,
                params={"entity_id": entity_id},
                param_types={"entity_id": spanner_v1.param_types.INT64},
            )
            entry_ids = [row[0] for row in results]

        if not entry_ids:
            return

        # Delete from AttributeValue table
        operation.delete(
            "AdvancedSearchAttributeValue",
            spanner_v1.KeySet(keys=[[entry_id] for entry_id in entry_ids]),
        )

        # Delete from Attribute table
        operation.delete(
            "AdvancedSearchAttribute",
            spanner_v1.KeySet(keys=[[entry_id] for entry_id in entry_ids]),
        )

        # Delete from Entry table
        operation.delete(
            "AdvancedSearchEntry", spanner_v1.KeySet(keys=[[entry_id] for entry_id in entry_ids])
        )

    def _build_search_query_conditions(
        self,
        entity_ids: list[int],
        attribute_names: list[str],
        entry_name_pattern: Optional[str] = None,
        hint_attrs: list[AttrHint] = [],
        join_attrs: list[AdvancedSearchJoinAttrInfo] = [],
    ) -> tuple[str, dict[str, Any], dict[str, Any]]:
        """Build common query conditions for search and count operations.

        Returns:
            tuple[str, dict[str, Any], dict[str, Any]]: A tuple containing:
                - The WHERE clause conditions (without JOIN conditions)
                - Query parameters
                - Parameter types
        """
        conditions = "e.OriginEntityId IN UNNEST(@entity_ids)"
        params: dict[str, Any] = {"entity_ids": entity_ids}
        param_types: dict[str, Any] = {
            "entity_ids": spanner_v1.param_types.Array(spanner_v1.param_types.INT64)
        }

        if attribute_names:
            conditions += """
                AND EXISTS (
                    SELECT 1
                    FROM AdvancedSearchAttribute a
                    WHERE a.EntryId = e.EntryId
                    AND a.Name IN UNNEST(@attribute_names)
                )"""
            params["attribute_names"] = attribute_names
            param_types["attribute_names"] = spanner_v1.param_types.Array(
                spanner_v1.param_types.STRING
            )

        # Add filter conditions based on hint_attrs
        for i, hint in enumerate(hint_attrs):
            if not hint.name:
                continue

            param_prefix = f"hint_{i}"
            match (hint.filter_key, hint.exact_match or False, hint.keyword):
                case (FilterKey.EMPTY, _, _):
                    conditions += f"""
                    AND EXISTS (
                        SELECT 1
                        FROM AdvancedSearchAttribute a2
                        WHERE a2.EntryId = e.EntryId
                        AND a2.Name = @{param_prefix}_name
                        AND NOT EXISTS (
                            SELECT 1
                            FROM AdvancedSearchAttributeValue v2
                            WHERE v2.EntryId = a2.EntryId
                            AND v2.AttributeId = a2.AttributeId
                            AND v2.Value != ''
                        )
                    )"""
                    params[f"{param_prefix}_name"] = hint.name
                    param_types[f"{param_prefix}_name"] = spanner_v1.param_types.STRING

                case (FilterKey.NON_EMPTY, _, _):
                    conditions += f"""
                    AND EXISTS (
                        SELECT 1
                        FROM AdvancedSearchAttribute a2
                        WHERE a2.EntryId = e.EntryId
                        AND a2.Name = @{param_prefix}_name
                        AND EXISTS (
                            SELECT 1
                            FROM AdvancedSearchAttributeValue v2
                            WHERE v2.EntryId = a2.EntryId
                            AND v2.AttributeId = a2.AttributeId
                            AND v2.Value != ''
                        )
                    )"""
                    params[f"{param_prefix}_name"] = hint.name
                    param_types[f"{param_prefix}_name"] = spanner_v1.param_types.STRING

                case (FilterKey.TEXT_CONTAINED, True, keyword) if keyword:
                    conditions += f"""
                    AND EXISTS (
                        SELECT 1
                        FROM AdvancedSearchAttribute a2
                        WHERE a2.EntryId = e.EntryId
                        AND a2.Name = @{param_prefix}_name
                        AND EXISTS (
                            SELECT 1
                            FROM AdvancedSearchAttributeValue v2
                            WHERE v2.EntryId = a2.EntryId
                            AND v2.AttributeId = a2.AttributeId
                            AND v2.Value = @{param_prefix}_value
                        )
                    )"""
                    params[f"{param_prefix}_name"] = hint.name
                    params[f"{param_prefix}_value"] = keyword
                    param_types[f"{param_prefix}_name"] = spanner_v1.param_types.STRING
                    param_types[f"{param_prefix}_value"] = spanner_v1.param_types.STRING

                case (FilterKey.TEXT_CONTAINED, False, keyword) if keyword:
                    conditions += f"""
                    AND EXISTS (
                        SELECT 1
                        FROM AdvancedSearchAttribute a2
                        WHERE a2.EntryId = e.EntryId
                        AND a2.Name = @{param_prefix}_name
                        AND EXISTS (
                            SELECT 1
                            FROM AdvancedSearchAttributeValue v2
                            WHERE v2.EntryId = a2.EntryId
                            AND v2.AttributeId = a2.AttributeId
                            AND LOWER(v2.Value) LIKE CONCAT('%', LOWER(@{param_prefix}_value), '%')
                        )
                    )"""
                    params[f"{param_prefix}_name"] = hint.name
                    params[f"{param_prefix}_value"] = keyword
                    param_types[f"{param_prefix}_name"] = spanner_v1.param_types.STRING
                    param_types[f"{param_prefix}_value"] = spanner_v1.param_types.STRING

                case (FilterKey.TEXT_NOT_CONTAINED, True, keyword) if keyword:
                    conditions += f"""
                    AND EXISTS (
                        SELECT 1
                        FROM AdvancedSearchAttribute a2
                        WHERE a2.EntryId = e.EntryId
                        AND a2.Name = @{param_prefix}_name
                        AND NOT EXISTS (
                            SELECT 1
                            FROM AdvancedSearchAttributeValue v2
                            WHERE v2.EntryId = a2.EntryId
                            AND v2.AttributeId = a2.AttributeId
                            AND v2.Value = @{param_prefix}_value
                        )
                    )"""
                    params[f"{param_prefix}_name"] = hint.name
                    params[f"{param_prefix}_value"] = keyword
                    param_types[f"{param_prefix}_name"] = spanner_v1.param_types.STRING
                    param_types[f"{param_prefix}_value"] = spanner_v1.param_types.STRING

                case (FilterKey.TEXT_NOT_CONTAINED, False, keyword) if keyword:
                    conditions += f"""
                    AND EXISTS (
                        SELECT 1
                        FROM AdvancedSearchAttribute a2
                        WHERE a2.EntryId = e.EntryId
                        AND a2.Name = @{param_prefix}_name
                        AND NOT EXISTS (
                            SELECT 1
                            FROM AdvancedSearchAttributeValue v2
                            WHERE v2.EntryId = a2.EntryId
                            AND v2.AttributeId = a2.AttributeId
                            AND LOWER(v2.Value) LIKE CONCAT('%', LOWER(@{param_prefix}_value), '%')
                        )
                    )"""
                    params[f"{param_prefix}_name"] = hint.name
                    params[f"{param_prefix}_value"] = keyword
                    param_types[f"{param_prefix}_name"] = spanner_v1.param_types.STRING
                    param_types[f"{param_prefix}_value"] = spanner_v1.param_types.STRING

                case (FilterKey.DUPLICATED, _, _):
                    conditions += f"""
                    AND EXISTS (
                        SELECT 1
                        FROM AdvancedSearchAttribute a2
                        JOIN AdvancedSearchAttributeValue v2
                            ON a2.EntryId = v2.EntryId
                            AND a2.AttributeId = v2.AttributeId
                        WHERE a2.Name = @{param_prefix}_name
                        GROUP BY v2.Value
                        HAVING COUNT(*) > 1
                    )"""
                    params[f"{param_prefix}_name"] = hint.name
                    param_types[f"{param_prefix}_name"] = spanner_v1.param_types.STRING

                case (FilterKey.CLEARED, _, _):
                    # Skip adding conditions for CLEARED as it matches all entries
                    pass

                case _:
                    # その他の場合は、単純に attribute_name の存在チェックのみ
                    conditions += f"""
                    AND EXISTS (
                        SELECT 1
                        FROM AdvancedSearchAttribute a2
                        WHERE a2.EntryId = e.EntryId
                        AND a2.Name = @{param_prefix}_name
                    )"""
                    params[f"{param_prefix}_name"] = hint.name
                    param_types[f"{param_prefix}_name"] = spanner_v1.param_types.STRING

        if len(join_attrs) > 0:
            conditions += """
                AND EXISTS (
                    SELECT 1
                    FROM
                        GRAPH_TABLE(
                            AdvancedSearchGraph
                            MATCH (src: AdvancedSearchEntry)-[referral:Referral]->
                            WHERE src.OriginEntityId IN UNNEST(@entity_ids)
                            RETURN referral.ReferralId AS ReferralEntryId,
                            referral.AttributeId AS SrcAttributeId
                        )
                    INNER JOIN AdvancedSearchAttribute AS a
                    ON a.EntryId = ReferralEntryId AND a.AttributeId = SrcAttributeId
                    WHERE
                        a.Name IN UNNEST(@joined_attribute_names)
                )"""
            params["joined_attribute_names"] = [attr.name for attr in join_attrs]
            param_types["joined_attribute_names"] = spanner_v1.param_types.Array(
                spanner_v1.param_types.STRING
            )

        # Add filter conditions based on join_attrs
        for i, join_attr in enumerate(join_attrs):
            if not join_attr.name:
                continue

            param_prefix = f"join_attr_{i}"

            # Process each attribute info in the join attributes
            for j, attr_info in enumerate(join_attr.attrinfo):
                attr_param_prefix = f"{param_prefix}_attr_{j}"

                match (attr_info.filter_key, attr_info.keyword):
                    case (FilterKey.EMPTY, _):
                        conditions += f"""
                            AND EXISTS (
                                SELECT 1
                                FROM
                                    GRAPH_TABLE(
                                        AdvancedSearchGraph
                                        MATCH (src: AdvancedSearchEntry)-[referral:Referral]->
                                        WHERE src.OriginEntityId IN UNNEST(@entity_ids)
                                        RETURN src.EntryId AS SrcEntryId,
                                        referral.AttributeId AS SrcAttributeId,
                                        referral.ReferralId AS ReferralEntryId
                                    )
                                INNER JOIN AdvancedSearchAttribute AS a
                                ON a.EntryId = ReferralEntryId AND a.AttributeId = SrcAttributeId
                                WHERE
                                    a.Name = @{attr_param_prefix}_name
                                    AND NOT EXISTS (
                                        SELECT 1
                                        FROM AdvancedSearchAttributeValue v
                                        WHERE v.EntryId = a.EntryId
                                        AND v.AttributeId = a.AttributeId
                                        AND v.Value != ''
                                    )
                            )"""
                        params[f"{attr_param_prefix}_name"] = attr_info.name
                        param_types[f"{attr_param_prefix}_name"] = spanner_v1.param_types.STRING

                    case (FilterKey.NON_EMPTY, _):
                        conditions += f"""
                            AND EXISTS (
                                SELECT 1
                                FROM
                                    GRAPH_TABLE(
                                        AdvancedSearchGraph
                                        MATCH (src: AdvancedSearchEntry)-[referral:Referral]->
                                        WHERE src.OriginEntityId IN UNNEST(@entity_ids)
                                        RETURN src.EntryId AS SrcEntryId,
                                        referral.AttributeId AS SrcAttributeId,
                                        referral.ReferralId AS ReferralEntryId
                                    )
                                INNER JOIN AdvancedSearchAttribute AS a
                                ON a.EntryId = ReferralEntryId AND a.AttributeId = SrcAttributeId
                                INNER JOIN AdvancedSearchAttributeValue v
                                ON v.EntryId = a.EntryId
                                AND v.AttributeId = a.AttributeId
                                WHERE
                                    a.Name = @{attr_param_prefix}_name
                                    AND v.Value != ''
                            )"""
                        params[f"{attr_param_prefix}_name"] = attr_info.name
                        param_types[f"{attr_param_prefix}_name"] = spanner_v1.param_types.STRING

                    case (FilterKey.TEXT_CONTAINED, keyword) if keyword:
                        conditions += f"""
                            AND EXISTS (
                                SELECT 1
                                FROM
                                    GRAPH_TABLE(
                                        AdvancedSearchGraph
                                        MATCH (src: AdvancedSearchEntry)-[referral:Referral]->
                                        WHERE src.OriginEntityId IN UNNEST(@entity_ids)
                                        RETURN src.EntryId AS SrcEntryId,
                                        referral.AttributeId AS SrcAttributeId,
                                        referral.ReferralId AS ReferralEntryId
                                    )
                                INNER JOIN AdvancedSearchAttribute AS a
                                ON a.EntryId = ReferralEntryId AND a.AttributeId = SrcAttributeId
                                INNER JOIN AdvancedSearchAttributeValue v
                                ON v.EntryId = a.EntryId
                                AND v.AttributeId = a.AttributeId
                                WHERE
                                    a.Name = @{attr_param_prefix}_name
                                    AND v.Value LIKE @{attr_param_prefix}_value
                            )"""
                        params[f"{attr_param_prefix}_name"] = attr_info.name
                        params[f"{attr_param_prefix}_value"] = f"%{keyword}%"
                        param_types[f"{attr_param_prefix}_name"] = spanner_v1.param_types.STRING
                        param_types[f"{attr_param_prefix}_value"] = spanner_v1.param_types.STRING

                    case (FilterKey.TEXT_NOT_CONTAINED, keyword) if keyword:
                        conditions += f"""
                            AND EXISTS (
                                SELECT 1
                                FROM
                                    GRAPH_TABLE(
                                        AdvancedSearchGraph
                                        MATCH (src: AdvancedSearchEntry)-[referral:Referral]->
                                        WHERE src.OriginEntityId IN UNNEST(@entity_ids)
                                        RETURN src.EntryId AS SrcEntryId,
                                        referral.AttributeId AS SrcAttributeId,
                                        referral.ReferralId AS ReferralEntryId
                                    )
                                INNER JOIN AdvancedSearchAttribute AS a
                                ON a.EntryId = ReferralEntryId AND a.AttributeId = SrcAttributeId
                                WHERE
                                    a.Name = @{attr_param_prefix}_name
                                    AND NOT EXISTS (
                                        SELECT 1
                                        FROM AdvancedSearchAttributeValue v
                                        WHERE v.EntryId = a.EntryId
                                        AND v.AttributeId = a.AttributeId
                                        AND v.Value LIKE @{attr_param_prefix}_value
                                    )
                            )"""
                        params[f"{attr_param_prefix}_name"] = attr_info.name
                        params[f"{attr_param_prefix}_value"] = f"%{keyword}%"
                        param_types[f"{attr_param_prefix}_name"] = spanner_v1.param_types.STRING
                        param_types[f"{attr_param_prefix}_value"] = spanner_v1.param_types.STRING

                    case (FilterKey.DUPLICATED, _):
                        conditions += f"""
                            AND EXISTS (
                                SELECT 1
                                FROM
                                    GRAPH_TABLE(
                                        AdvancedSearchGraph
                                        MATCH (src: AdvancedSearchEntry)-[referral:Referral]->
                                        WHERE src.OriginEntityId IN UNNEST(@entity_ids)
                                        RETURN src.EntryId AS SrcEntryId,
                                        referral.AttributeId AS SrcAttributeId,
                                        referral.ReferralId AS ReferralEntryId
                                    )
                                INNER JOIN AdvancedSearchAttribute AS a
                                ON a.EntryId = ReferralEntryId AND a.AttributeId = SrcAttributeId
                                INNER JOIN AdvancedSearchAttributeValue v1
                                ON v1.EntryId = a.EntryId
                                AND v1.AttributeId = a.AttributeId
                                WHERE
                                    a.Name = @{attr_param_prefix}_name
                                    AND EXISTS (
                                        SELECT 1
                                        FROM AdvancedSearchAttributeValue v2
                                        INNER JOIN AdvancedSearchAttribute a2
                                        ON v2.EntryId = a2.EntryId
                                        AND v2.AttributeId = a2.AttributeId
                                        WHERE a2.Name = a.Name
                                        AND v2.Value = v1.Value
                                        AND v2.EntryId != v1.EntryId
                                    )
                            )"""
                        params[f"{attr_param_prefix}_name"] = attr_info.name
                        param_types[f"{attr_param_prefix}_name"] = spanner_v1.param_types.STRING

                    case (FilterKey.CLEARED, _):
                        conditions += f"""
                            AND EXISTS (
                                SELECT 1
                                FROM
                                    GRAPH_TABLE(
                                        AdvancedSearchGraph
                                        MATCH (src: AdvancedSearchEntry)-[referral:Referral]->
                                        WHERE src.OriginEntityId IN UNNEST(@entity_ids)
                                        RETURN src.EntryId AS SrcEntryId,
                                        referral.AttributeId AS SrcAttributeId,
                                        referral.ReferralId AS ReferralEntryId
                                    )
                                INNER JOIN AdvancedSearchAttribute AS a
                                ON a.EntryId = ReferralEntryId AND a.AttributeId = SrcAttributeId
                                WHERE
                                    a.Name = @{attr_param_prefix}_name
                                    AND NOT EXISTS (
                                        SELECT 1
                                        FROM AdvancedSearchAttributeValue v
                                        WHERE v.EntryId = a.EntryId
                                        AND v.AttributeId = a.AttributeId
                                    )
                            )"""
                        params[f"{attr_param_prefix}_name"] = attr_info.name
                        param_types[f"{attr_param_prefix}_name"] = spanner_v1.param_types.STRING

        if entry_name_pattern:
            conditions += " AND LOWER(e.Name) LIKE CONCAT('%', LOWER(@name_pattern), '%')"
            params["name_pattern"] = entry_name_pattern

        return conditions, params, param_types

    def search_entries(
        self,
        entity_ids: list[int],
        attribute_names: list[str],
        entry_name_pattern: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        hint_attrs: list[AttrHint] = [],
        join_attrs: list[AdvancedSearchJoinAttrInfo] = [],
    ) -> list[AdvancedSearchEntry]:
        """Search entries based on criteria"""
        conditions, params, param_types = self._build_search_query_conditions(
            entity_ids, attribute_names, entry_name_pattern, hint_attrs, join_attrs
        )

        query = f"""
        SELECT DISTINCT e.*
        FROM AdvancedSearchEntry e
        WHERE {conditions}
        LIMIT @limit OFFSET @offset
        """

        params.update({"limit": limit, "offset": offset})
        param_types.update(
            {"limit": spanner_v1.param_types.INT64, "offset": spanner_v1.param_types.INT64}
        )

        with self.database.snapshot() as snapshot:
            results = snapshot.execute_sql(query, params=params, param_types=param_types)
            return [
                AdvancedSearchEntry(
                    entry_id=row[0], name=row[1], origin_entity_id=row[2], origin_entry_id=row[3]
                )
                for row in results
            ]

    def count_entries(
        self,
        entity_ids: list[int],
        attribute_names: list[str],
        entry_name_pattern: Optional[str] = None,
        hint_attrs: list[AttrHint] = [],
        join_attrs: list[AdvancedSearchJoinAttrInfo] = [],
    ) -> int:
        """Count total number of entries matching the search criteria"""
        conditions, params, param_types = self._build_search_query_conditions(
            entity_ids, attribute_names, entry_name_pattern, hint_attrs, join_attrs
        )

        query = f"""
        SELECT COUNT(*)
        FROM AdvancedSearchEntry e
        WHERE {conditions}
        """

        with self.database.snapshot() as snapshot:
            results = snapshot.execute_sql(query, params=params, param_types=param_types)
            # StreamedResultSet needs to be consumed using its iterator
            for row in results:
                return row[0]  # Return the first (and only) row's first column
            return 0  # Return 0 if no results found

    def get_entry_attributes(
        self,
        entry_ids: list[str],
        attribute_names: list[str] | None = None,
        join_attrs: list[AdvancedSearchJoinAttrInfo] = [],
    ) -> list[tuple[AdvancedSearchAttribute, AdvancedSearchAttributeValue]]:
        """Get attributes and their values for given entries"""

        base_query = """
        SELECT
          a.EntryId,
          a.AttributeId,
          a.Type,
          a.Name,
          a.OriginEntityAttrId,
          a.OriginAttributeId,
          v.AttributeValueId,
          v.Value,
          v.RawValue,
          FALSE AS IsJoinedAttr,
        FROM
          AdvancedSearchAttribute a
        JOIN
          AdvancedSearchAttributeValue v
        ON
          a.EntryId = v.EntryId
          AND a.AttributeId = v.AttributeId
        WHERE
          a.EntryId IN UNNEST(@entry_ids)
        """
        join_attr_query = """
        SELECT
          a.EntryId,
          a.AttributeId,
          a.Type,
          a.Name,
          a.OriginEntityAttrId,
          a.OriginAttributeId,
          v.AttributeValueId,
          v.Value,
          v.RawValue,
          TRUE AS IsJoinedAttr,
        FROM
          GRAPH_TABLE(
         AdvancedSearchGraph
        MATCH (src: AdvancedSearchEntry)-[referral:Referral]->
        WHERE src.EntryId IN UNNEST(@entry_ids)
        RETURN src.EntryId AS SrcEntryId,
        referral.AttributeId AS SrcAttributeId,
        referral.ReferralId AS ReferralEntryId
        )
        INNER JOIN AdvancedSearchAttribute AS a
        ON
          a.EntryId = ReferralEntryId AND a.AttributeId = SrcAttributeId
        JOIN
          AdvancedSearchAttributeValue v
        ON
          a.EntryId = v.EntryId
          AND a.AttributeId = v.AttributeId
        """
        params = {"entry_ids": entry_ids}
        param_types = {"entry_ids": spanner_v1.param_types.Array(spanner_v1.param_types.STRING)}

        if attribute_names:
            base_query += " AND a.Name IN UNNEST(@attribute_names)"
            params["attribute_names"] = attribute_names
            param_types["attribute_names"] = spanner_v1.param_types.Array(
                spanner_v1.param_types.STRING
            )

        # FIXME filter with appropriate attr name
        if len(join_attrs) == 0:
            join_attr_query += "WHERE a.Name IN UNNEST(@join_attr_names)"
            params["join_attr_names"] = [
                attrinfo.name for attr in join_attrs for attrinfo in attr.attrinfo
            ]
            param_types["join_attr_names"] = spanner_v1.param_types.Array(
                spanner_v1.param_types.STRING
            )

        with self.database.snapshot() as snapshot:
            query = f"{base_query} UNION ALL {join_attr_query}"
            results = snapshot.execute_sql(query, params=params, param_types=param_types)

            def _parse_raw_value(raw_value: Any) -> Optional[dict[str, Any] | list[Any]]:
                if isinstance(raw_value, spanner_v1.data_types.JsonObject):
                    if raw_value._is_array:
                        return raw_value._array_value
                return raw_value

            # TODO cover join attrs
            return [
                (
                    AdvancedSearchAttribute(
                        entry_id=row[0],
                        attribute_id=row[1],
                        type=AttrType(row[2]),
                        name=row[3],
                        origin_entity_attr_id=row[4],
                        origin_attribute_id=row[5],
                    ),
                    AdvancedSearchAttributeValue(
                        entry_id=row[0],
                        attribute_id=row[1],
                        attribute_value_id=row[6],
                        value=str(row[7]),
                        raw_value=_parse_raw_value(row[8]),
                    ),
                )
                for row in results
                if not row[9]
            ]

    def get_referrals(
        self,
        entry_ids: list[str],
        referral_pattern: str | None = None,
        referral_entity_id: int | None = None,
    ) -> dict[str, list[dict[str, Any]]]:
        """Get referrals for given entries"""

        query = """
        SELECT DISTINCT
            v.EntryId,
            v.Value
        FROM AdvancedSearchAttributeValue v
        JOIN AdvancedSearchAttribute a ON v.EntryId = a.EntryId AND v.AttributeId = a.AttributeId
        WHERE v.EntryId IN UNNEST(@entry_ids)
        AND a.Type = @ref_type
        """
        params: dict[str, Any] = {
            "entry_ids": entry_ids,
            "ref_type": AttrType.OBJECT.value,
        }
        param_types: dict[str, Any] = {
            "entry_ids": spanner_v1.param_types.Array(spanner_v1.param_types.STRING),
            "ref_type": spanner_v1.param_types.INT64,
        }

        if referral_pattern:
            query += " AND JSON_VALUE(v.Value, '$.value.name') LIKE CONCAT('%', @pattern, '%')"
            params["pattern"] = referral_pattern

        if referral_entity_id:
            query += " AND CAST(JSON_VALUE(v.Value, '$.value.entity_id') AS INT64) = @entity_id"
            params["entity_id"] = referral_entity_id

        referrals: dict[str, list[dict[str, Any]]] = {}
        with self.database.snapshot() as snapshot:
            results = snapshot.execute_sql(query, params=params, param_types=param_types)
            for row in results:
                entry_id, value_json = row
                if entry_id not in referrals:
                    referrals[entry_id] = []
                if value_json:
                    value = json.loads(value_json)
                    if (
                        isinstance(value, dict)
                        and "value" in value
                        and isinstance(value["value"], dict)
                    ):
                        value_data = value["value"]
                        if "id" in value_data and "name" in value_data:
                            referrals[entry_id].append(
                                {
                                    "id": value_data["id"],
                                    "name": value_data["name"],
                                }
                            )
        return referrals

    def get_joined_entries(
        self,
        prev_results: list[AdvancedSearchResultRecord],
        join_attr: AdvancedSearchJoinAttrInfo,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[bool, dict[str, Any]]:
        """Get joined entries from previous search results.

        Args:
            prev_results: Previous search results
            join_attr: Join attribute information
            limit: Maximum number of results to return
            offset: Offset for pagination

        Returns:
            Tuple of (will_filter_by_joined_attr, search_results)
        """
        # Get entity IDs from previous results
        entity_ids = [result.entity["id"] for result in prev_results]

        # Fetch all required data in a single query
        with self.database.snapshot() as snapshot:
            values = list(
                snapshot.execute_sql(
                    """
                WITH source_entries AS (
                    SELECT EntryId, OriginEntityId
                    FROM AdvancedSearchEntry
                    WHERE OriginEntityId IN UNNEST(@entity_ids)
                ),
                source_values AS (
                    SELECT av.RawValue, av.Value, a.EntryId, a.Type
                    FROM source_entries se
                    JOIN AdvancedSearchAttribute a ON se.EntryId = a.EntryId
                    JOIN AdvancedSearchAttributeValue av
                        ON a.EntryId = av.EntryId
                        AND a.AttributeId = av.AttributeId
                    WHERE a.Name = @attr_name
                )
                SELECT
                    sv.RawValue,
                    sv.Value,
                    sv.EntryId,
                    sv.Type,
                    je.EntryId as JoinedEntryId,
                    je.Name as JoinedName,
                    je.OriginEntityId as JoinedOriginEntityId,
                    je.OriginEntryId as JoinedOriginEntryId,
                    ja.Name as JoinedAttrName,
                    ja.Type as JoinedAttrType,
                    jav.RawValue as JoinedRawValue,
                    jav.Value as JoinedValue
                FROM source_values sv
                LEFT JOIN AdvancedSearchEntry je
                    ON je.OriginEntryId = CAST(JSON_VALUE(sv.RawValue, '$.id') AS INT64)
                LEFT JOIN AdvancedSearchAttribute ja
                    ON je.EntryId = ja.EntryId
                    AND ja.Name IN UNNEST(@attr_names)
                LEFT JOIN AdvancedSearchAttributeValue jav
                    ON ja.EntryId = jav.EntryId
                    AND ja.AttributeId = jav.AttributeId
                """,
                    params={
                        "entity_ids": entity_ids,
                        "attr_name": join_attr.name,
                        "attr_names": [attr.name for attr in join_attr.attrinfo],
                    },
                    param_types={
                        "entity_ids": spanner_v1.param_types.Array(spanner_v1.param_types.INT64),
                        "attr_name": spanner_v1.param_types.STRING,
                        "attr_names": spanner_v1.param_types.Array(spanner_v1.param_types.STRING),
                    },
                )
            )

            join_entries_dict: dict[int, dict[str, Any]] = {}

            for value in values:
                joined_entry_id = value[4]
                joined_name = value[5]
                joined_origin_entity_id = value[6]
                joined_origin_entry_id = value[7]
                joined_attr_name = value[8]
                joined_attr_type = value[9] if value[9] is not None else None
                joined_raw_value = value[10]
                joined_value = value[11]

                # Skip if no joined entry found
                if not joined_entry_id:
                    continue

                # Add joined entry information
                if joined_origin_entry_id not in join_entries_dict:
                    join_entries_dict[joined_origin_entry_id] = {
                        "entity": {
                            "id": joined_origin_entity_id,
                            "name": f"Entity_{joined_origin_entity_id}",
                        },
                        "entry": {
                            "id": joined_origin_entry_id,
                            "name": joined_name,
                        },
                        "attrs": {},
                        "is_readable": True,
                        "referrals": [],
                    }

                # Add attribute values
                if joined_attr_name and joined_attr_type is not None:
                    join_entries_dict[joined_origin_entry_id]["attrs"][joined_attr_name] = {
                        "type": AttrType(joined_attr_type),
                        "value": joined_raw_value if joined_raw_value is not None else joined_value,
                        "is_readable": True,
                    }

            # Determine if filtering is required based on join attributes
            will_filter = any(
                bool(x.keyword) or (x.filter_key or 0) > 0 for x in join_attr.attrinfo
            )

            return will_filter, {
                "ret_count": len(join_entries_dict),
                "ret_values": list(join_entries_dict.values()),
            }

    def get_entry_id_mapping(self, origin_entry_ids: list[int]) -> dict[int, str]:
        """Get mapping from OriginEntryId to EntryId.

        Args:
            origin_entry_ids: List of original entry IDs from Django

        Returns:
            Dictionary mapping OriginEntryId to EntryId
        """
        if not origin_entry_ids:
            return {}

        query = """
        SELECT OriginEntryId, EntryId
        FROM AdvancedSearchEntry
        WHERE OriginEntryId IN UNNEST(@origin_entry_ids)
        """
        params = {"origin_entry_ids": origin_entry_ids}
        param_types = {
            "origin_entry_ids": spanner_v1.param_types.Array(spanner_v1.param_types.INT64)
        }

        with self.database.snapshot() as snapshot:
            results = snapshot.execute_sql(query, params=params, param_types=param_types)
            return {row[0]: row[1] for row in results}
