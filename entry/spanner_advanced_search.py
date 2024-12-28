import json
from typing import Any, Optional, Protocol

from google.cloud import spanner_v1
from google.cloud.spanner_v1.database import Database
from google.cloud.spanner_v1.instance import Instance
from pydantic import BaseModel, Field

from airone.lib.types import AttrType


class SpannerBatch(Protocol):
    """Protocol for Spanner batch operations"""

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
    origin_entity_attr_id: int = Field(description="Original entity attribute ID from Django")
    origin_attribute_id: int = Field(description="Original attribute ID from Django")


class AdvancedSearchAttributeValue(BaseModel):
    """Represents an attribute value in the advanced search system"""

    entry_id: str = Field(description="UUID of the parent entry")
    attribute_id: str = Field(description="UUID of the parent attribute")
    attribute_value_id: str = Field(description="UUID of the attribute value")
    key: str = Field(max_length=512, description="Search key for the value")
    value: Optional[Any] = Field(description="JSON value data")


# Repository interface
class SpannerRepository:
    """Repository for interacting with Cloud Spanner"""

    def __init__(self, project_id: str, instance_id: str, database_id: str):
        self.client: spanner_v1.Client = spanner_v1.Client(project=project_id)
        self.instance: Instance = self.client.instance(instance_id)
        self.database: Database = self.instance.database(database_id)

    def insert_entries(self, entries: list[AdvancedSearchEntry], batch: SpannerBatch) -> None:
        """Insert multiple entries in a batch"""
        if not entries:
            return

        batch.insert(
            table="AdvancedSearchEntry",
            columns=("EntryId", "Name", "OriginEntityId", "OriginEntryId"),
            values=[
                (entry.entry_id, entry.name, entry.origin_entity_id, entry.origin_entry_id)
                for entry in entries
            ],
        )

    def insert_attributes(self, attrs: list[AdvancedSearchAttribute], batch: SpannerBatch) -> None:
        """Insert multiple attributes in a batch"""
        if not attrs:
            return

        batch.insert(
            table="AdvancedSearchAttribute",
            columns=(
                "EntryId",
                "AttributeId",
                "Type",
                "OriginEntityAttrId",
                "OriginAttributeId",
            ),
            values=[
                (
                    attr.entry_id,
                    attr.attribute_id,
                    attr.type.value,
                    attr.origin_entity_attr_id,
                    attr.origin_attribute_id,
                )
                for attr in attrs
            ],
        )

    def insert_attribute_values(
        self, values: list[AdvancedSearchAttributeValue], batch: SpannerBatch
    ) -> None:
        """Insert multiple attribute values in a batch"""
        if not values:
            return

        batch.insert(
            table="AdvancedSearchAttributeValue",
            columns=("EntryId", "AttributeId", "AttributeValueId", "Key", "Value"),
            values=[
                (
                    value.entry_id,
                    value.attribute_id,
                    value.attribute_value_id,
                    value.key,
                    json.dumps(value.value) if value.value is not None else None,
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

    def delete_entries_by_entity(self, entity_id: int, batch: SpannerBatch) -> None:
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
        batch.delete(
            "AdvancedSearchAttributeValue",
            spanner_v1.KeySet(keys=[[entry_id] for entry_id in entry_ids]),
        )

        # Delete from Attribute table
        batch.delete(
            "AdvancedSearchAttribute",
            spanner_v1.KeySet(keys=[[entry_id] for entry_id in entry_ids]),
        )

        # Delete from Entry table
        batch.delete(
            "AdvancedSearchEntry", spanner_v1.KeySet(keys=[[entry_id] for entry_id in entry_ids])
        )

    def search_entries(
        self,
        entity_ids: list[int],
        attribute_names: list[str],
        entry_name_pattern: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AdvancedSearchEntry]:
        """Search entries based on criteria"""
        query = """
        SELECT DISTINCT e.*
        FROM AdvancedSearchEntry e
        JOIN AdvancedSearchAttribute a ON e.EntryId = a.EntryId
        JOIN AdvancedSearchAttributeValue v ON
            a.EntryId = v.EntryId AND
            a.AttributeId = v.AttributeId
        WHERE e.OriginEntityId IN UNNEST(@entity_ids)
        """
        params: dict[str, Any] = {"entity_ids": entity_ids}
        param_types: dict[str, Any] = {
            "entity_ids": spanner_v1.param_types.Array(spanner_v1.param_types.INT64)
        }

        if entry_name_pattern:
            query += " AND LOWER(e.Name) LIKE CONCAT('%', LOWER(@name_pattern), '%')"
            params["name_pattern"] = entry_name_pattern

        query += " LIMIT @limit OFFSET @offset"
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

    def get_entry_attributes(
        self,
        entry_ids: list[str],
        attribute_names: list[str] | None = None,
    ) -> list[tuple[AdvancedSearchAttribute, AdvancedSearchAttributeValue]]:
        """Get attributes and their values for given entries"""
        import json

        query = """
        SELECT a.*, v.*
        FROM AdvancedSearchAttribute a
        JOIN AdvancedSearchAttributeValue v
            ON a.EntryId = v.EntryId AND a.AttributeId = v.AttributeId
        WHERE a.EntryId IN UNNEST(@entry_ids)
        """
        params = {"entry_ids": entry_ids}
        param_types = {"entry_ids": spanner_v1.param_types.Array(spanner_v1.param_types.STRING)}

        with self.database.snapshot() as snapshot:
            results = snapshot.execute_sql(query, params=params, param_types=param_types)
            return [
                (
                    AdvancedSearchAttribute(
                        entry_id=row[0],
                        attribute_id=row[1],
                        type=row[2],
                        origin_entity_attr_id=row[3],
                        origin_attribute_id=row[4],
                    ),
                    AdvancedSearchAttributeValue(
                        entry_id=row[5],
                        attribute_id=row[6],
                        attribute_value_id=row[7],
                        key=row[8],
                        value=json.loads(row[9]) if row[9] is not None else None,
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
