CREATE TABLE AdvancedSearchEntry (
    EntryId STRING(36) NOT NULL,
    Name STRING(200) NOT NULL,
    OriginEntityId INT64 NOT NULL,
    OriginEntryId INT64 NOT NULL
) PRIMARY KEY (EntryId);

CREATE INDEX idx_entry_name ON AdvancedSearchEntry(Name);

CREATE TABLE AdvancedSearchAttribute (
    EntryId STRING(36) NOT NULL,
    AttributeId STRING(36) NOT NULL,
    Type INT64 NOT NULL,
    OriginEntityAttrId INT64 NOT NULL,
    OriginAttributeId INT64 NOT NULL
) PRIMARY KEY (EntryId, AttributeId),
  INTERLEAVE IN PARENT AdvancedSearchEntry ON DELETE CASCADE;

CREATE TABLE AdvancedSearchAttributeValue (
    EntryId STRING(36) NOT NULL,
    AttributeId STRING(36) NOT NULL,
    AttributeValueId STRING(36) NOT NULL,
    Key STRING(512) NOT NULL,
    Value JSON
) PRIMARY KEY (EntryId, AttributeId, AttributeValueId),
  INTERLEAVE IN PARENT AdvancedSearchAttribute ON DELETE CASCADE;

CREATE INDEX idx_attribute_value_key ON AdvancedSearchAttributeValue(Key);
