-- Insert attribute values
INSERT INTO AdvancedSearchAttributeValue
    (EntryId, AttributeId, AttributeValueId, Key, Value)
VALUES
    -- String values
    ('entry-001', 'attr-001', 'val-001', 'string_value_IcbCckjFkF', NULL),
    
    -- Reference Entry values
    ('entry-001', 'attr-002', 'val-002', 'Referred_Entry_20240831125227_0', 
     JSON '{"id": 2, "name": "Referred_Entry_20240831125227_0"}'),
    
    -- Named Object values
    ('entry-001', 'attr-003', 'val-003', 'named_object_value_KRvJzeBxWW',
     JSON '{"named_object_value_KRvJzeBxWW": {"id": 3, "name": "Referred_Entry_20240831125227_1"}}'),
    
    -- Group reference
    ('entry-001', 'attr-004', 'val-004', 'Referred_Group_20240831125227_1',
     JSON '{"id": 2, "name": "Referred_Group_20240831125227_1"}'),
    
    -- Array string values
    ('entry-001', 'attr-006', 'val-006', 'array_string_value_zDFhOlngGo_0,array_string_value_zDFhOlngGo_1',
     JSON '["array_string_value_zDFhOlngGo_0", "array_string_value_zDFhOlngGo_1"]'),
    
    -- Simple values
    ('entry-001', 'attr-007', 'val-007', 'text_value_VCxNkDBNUv', NULL),
    ('entry-001', 'attr-008', 'val-008', 'true', NULL),
    ('entry-001', 'attr-009', 'val-009', '2024-08-31', NULL),
    ('entry-001', 'attr-010', 'val-010', '2024-08-31T03:52:30.174553+00:00', NULL),
    
    -- Values for entry-002
    ('entry-002', 'attr-011', 'val-011', 'string_value_FdaphNTQtE', NULL),
    ('entry-002', 'attr-012', 'val-012', 'Referred_Entry_20240831125227_0',
     JSON '{"id": 2, "name": "Referred_Entry_20240831125227_0"}');
