CREATE TABLE AdvancedSearchEntry (
    EntryId STRING(36) NOT NULL,
    Name STRING(200) NOT NULL,
    OriginEntityId INT64 NOT NULL,
    OriginEntryId INT64 NOT NULL
) PRIMARY KEY (EntryId);

CREATE INDEX AdvancedSearchEntryNameIndex ON AdvancedSearchEntry(Name);

CREATE INDEX AdvancedSearchEntryOriginEntityIdIndex ON AdvancedSearchEntry(OriginEntityId);

CREATE TABLE AdvancedSearchAttribute (
    EntryId STRING(36) NOT NULL,
    AttributeId STRING(36) NOT NULL,
    Type INT64 NOT NULL,
    Name STRING(200) NOT NULL,
    OriginEntityAttrId INT64 NOT NULL,
    OriginAttributeId INT64 NOT NULL
) PRIMARY KEY (EntryId, AttributeId),
  INTERLEAVE IN PARENT AdvancedSearchEntry ON DELETE CASCADE;

CREATE INDEX AdvancedSearchAttributeNameEntryIdIndex ON AdvancedSearchAttribute(Name, EntryId);

CREATE TABLE AdvancedSearchAttributeValue (
    EntryId STRING(36) NOT NULL,
    AttributeId STRING(36) NOT NULL,
    AttributeValueId STRING(36) NOT NULL,
    Value STRING(MAX) NOT NULL,
    RawValue JSON
) PRIMARY KEY (EntryId, AttributeId, AttributeValueId),
  INTERLEAVE IN PARENT AdvancedSearchAttribute ON DELETE CASCADE;

CREATE INDEX AdvancedSearchAttributeValueParentKeyIndex ON AdvancedSearchAttributeValue(EntryId, AttributeId);

CREATE TABLE AdvancedSearchEntryReferral (
    EntryId STRING(36) NOT NULL,
    AttributeId STRING(36) NOT NULL,
    ReferralId STRING(36) NOT NULL,
    FOREIGN KEY (EntryId) REFERENCES AdvancedSearchEntry (EntryId),
    FOREIGN KEY (EntryId, AttributeId) REFERENCES AdvancedSearchAttribute (EntryId, AttributeId),
    FOREIGN KEY (ReferralId) REFERENCES AdvancedSearchEntry (EntryId)
) PRIMARY KEY (EntryId, AttributeId, ReferralId);

CREATE PROPERTY GRAPH AdvancedSearchGraph
  NODE TABLES (AdvancedSearchEntry)
  EDGE TABLES (
    AdvancedSearchEntryReferral
      SOURCE KEY (EntryId) REFERENCES AdvancedSearchEntry (EntryId)
      DESTINATION KEY (ReferralId) REFERENCES AdvancedSearchEntry (EntryId)
      LABEL Referral
  );
