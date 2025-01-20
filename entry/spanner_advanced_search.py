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
    ) -> tuple[str, dict[str, Any], dict[str, Any]]:
        """Build common query conditions for search and count operations.

        Returns:
            tuple[str, dict[str, Any], dict[str, Any]]: A tuple containing:
                - The WHERE clause and JOIN conditions
                - Query parameters
                - Parameter types
        """
        conditions = "WHERE e.OriginEntityId IN UNNEST(@entity_ids)"
        params: dict[str, Any] = {"entity_ids": entity_ids}
        param_types: dict[str, Any] = {
            "entity_ids": spanner_v1.param_types.Array(spanner_v1.param_types.INT64)
        }

        if attribute_names:
            conditions += " AND a.Name IN UNNEST(@attribute_names)"
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
    ) -> list[AdvancedSearchEntry]:
        """Search entries based on criteria"""
        conditions, params, param_types = self._build_search_query_conditions(
            entity_ids, attribute_names, entry_name_pattern, hint_attrs
        )

        query = f"""
        SELECT DISTINCT e.*
        FROM AdvancedSearchEntry e
        JOIN AdvancedSearchAttribute a ON e.EntryId = a.EntryId
        JOIN AdvancedSearchAttributeValue v ON
            a.EntryId = v.EntryId AND
            a.AttributeId = v.AttributeId
        {conditions}
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
    ) -> int:
        """Count total number of entries matching the search criteria"""
        conditions, params, param_types = self._build_search_query_conditions(
            entity_ids, attribute_names, entry_name_pattern, hint_attrs
        )

        query = f"""
        SELECT COUNT(DISTINCT e.EntryId)
        FROM AdvancedSearchEntry e
        JOIN AdvancedSearchAttribute a ON e.EntryId = a.EntryId
        JOIN AdvancedSearchAttributeValue v ON
            a.EntryId = v.EntryId AND
            a.AttributeId = v.AttributeId
        {conditions}
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
    ) -> list[tuple[AdvancedSearchAttribute, AdvancedSearchAttributeValue]]:
        """Get attributes and their values for given entries"""

        query = """
        SELECT a.*, v.*
        FROM AdvancedSearchAttribute a
        JOIN AdvancedSearchAttributeValue v
            ON a.EntryId = v.EntryId AND a.AttributeId = v.AttributeId
        WHERE a.EntryId IN UNNEST(@entry_ids)
        """
        params = {"entry_ids": entry_ids}
        param_types = {"entry_ids": spanner_v1.param_types.Array(spanner_v1.param_types.STRING)}

        if attribute_names:
            query += " AND a.Name IN UNNEST(@attribute_names)"
            params["attribute_names"] = attribute_names
            param_types["attribute_names"] = spanner_v1.param_types.Array(
                spanner_v1.param_types.STRING
            )

        with self.database.snapshot() as snapshot:
            results = snapshot.execute_sql(query, params=params, param_types=param_types)

            def _parse_raw_value(raw_value: Any) -> Optional[dict[str, Any] | list[Any]]:
                if isinstance(raw_value, spanner_v1.data_types.JsonObject):
                    if raw_value._is_array:
                        return raw_value._array_value
                return raw_value

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
                        entry_id=row[6],
                        attribute_id=row[7],
                        attribute_value_id=row[8],
                        value=str(row[9]),
                        raw_value=_parse_raw_value(row[10]),
                    ),
                )
                for row in results
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
        join_attr: dict[str, Any],
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[bool, dict[str, Any]]:
        """Get joined entries for join_attrs functionality.
        This is similar to _get_joined_resp in the original implementation.

        Args:
            prev_results: Previous search results
            join_attr: Join attribute configuration
            limit: Result limit
            offset: Result offset

        Returns:
            tuple[bool, dict[str, Any]]: A tuple containing:
                - Whether to filter by joined attributes
                - Search results for joined entries
        """
        # Get entity IDs and entry names from previous results
        item_names: list[str] = []
        hint_entity_ids: list[int] = []

        # First get all attributes matching the join attribute name
        query = """
        SELECT
            a.Type,
            a.OriginEntityAttrId,
            v.Value,
            v.RawValue
        FROM (
            SELECT DISTINCT
                EntryId,
                Type,
                OriginEntityAttrId,
                AttributeId
            FROM AdvancedSearchAttribute
            WHERE Name = @attr_name
            AND Type & @object_type != 0
        ) a
        JOIN AdvancedSearchAttributeValue v
            ON a.EntryId = v.EntryId
            AND a.AttributeId = v.AttributeId
        """
        params = {
            "attr_name": join_attr["name"],
            "object_type": AttrType.OBJECT.value,
        }
        param_types = {
            "attr_name": spanner_v1.param_types.STRING,
            "object_type": spanner_v1.param_types.INT64,
        }

        with self.database.snapshot() as snapshot:
            results = snapshot.execute_sql(query, params=params, param_types=param_types)
            for row in results:
                attr_type, entity_attr_id, value, raw_value = row
                if raw_value:
                    # Handle Spanner JsonObject type
                    if isinstance(raw_value, spanner_v1.data_types.JsonObject):
                        raw_value_dict = (
                            raw_value._array_value if raw_value._is_array else raw_value
                        )
                    else:
                        raw_value_dict = raw_value

                    if isinstance(raw_value_dict, dict):
                        # Handle different object types
                        if attr_type == AttrType.OBJECT.value:
                            if value and value not in item_names:
                                item_names.append(value)
                        elif attr_type == AttrType.NAMED_OBJECT.value:
                            for co_info in raw_value_dict.values():
                                if (
                                    isinstance(co_info, dict)
                                    and co_info.get("name") not in item_names
                                ):
                                    item_names.append(co_info["name"])
                        elif attr_type == AttrType.ARRAY_OBJECT.value:
                            for r in raw_value_dict:
                                if isinstance(r, dict) and r.get("name") not in item_names:
                                    item_names.append(r["name"])
                        elif attr_type == AttrType.ARRAY_NAMED_OBJECT.value:
                            for r in raw_value_dict:
                                if isinstance(r, dict):
                                    [co_info] = r.values()
                                    if (
                                        isinstance(co_info, dict)
                                        and co_info.get("name") not in item_names
                                    ):
                                        item_names.append(co_info["name"])

                # Add entity attr IDs for referral lookup
                if entity_attr_id and entity_attr_id not in hint_entity_ids:
                    hint_entity_ids.append(entity_attr_id)

        # Convert hint_attrs for the join
        hint_attrs: list[AttrHint] = []
        for info in join_attr.get("attrinfo", []):
            hint_attrs.append(
                AttrHint(
                    name=info["name"],
                    keyword=info.get("keyword"),
                    filter_key=info.get("filter_key"),
                )
            )

        # Search entries that match the join criteria
        results = self.search_entries(
            entity_ids=list(set(hint_entity_ids)),
            attribute_names=[x.name for x in hint_attrs if x.name],
            entry_name_pattern="|".join(item_names) if item_names else None,
            limit=limit,
            offset=join_attr.get("offset", 0),
            hint_attrs=hint_attrs,
        )

        # Get attributes for the found entries
        entry_ids = [entry.entry_id for entry in results]
        attr_values = self.get_entry_attributes(
            entry_ids,
            attribute_names=[x.name for x in hint_attrs if x.name],
        )

        # Convert results to the expected format
        attrs_by_entry: dict[str, dict[str, dict]] = {}
        for attr, value in attr_values:
            if attr.entry_id not in attrs_by_entry:
                attrs_by_entry[attr.entry_id] = {}
            attrs_by_entry[attr.entry_id][attr.name] = {
                "type": attr.type,
                "value": value.raw_value if value.raw_value else value.value,
                "is_readable": True,
            }

        ret_values = []
        for entry in results:
            ret_values.append(
                {
                    "entry": {
                        "id": entry.origin_entry_id,
                        "name": entry.name,
                    },
                    "attrs": attrs_by_entry.get(entry.entry_id, {}),
                }
            )

        return (
            # Whether to filter by joined attributes
            any(
                x.get("keyword") or x.get("filter_key", 0) > 0
                for x in join_attr.get("attrinfo", [])
            ),
            {
                "ret_values": ret_values,
                "ret_count": len(ret_values),
            },
        )
