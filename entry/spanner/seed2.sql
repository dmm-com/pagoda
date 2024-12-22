-- Insert attributes
INSERT INTO AdvancedSearchAttribute
    (EntryId, AttributeId, Type, OriginEntityAttrId, OriginAttributeId)
VALUES
    -- For entry-001
    ('entry-001', 'attr-001', 2, 5, 44),    -- String type
    ('entry-001', 'attr-002', 1, 6, 56),    -- Reference Entry type
    ('entry-001', 'attr-003', 2049, 7, 70), -- Named Object type
    ('entry-001', 'attr-004', 16, 8, 82),   -- Group type
    ('entry-001', 'attr-005', 64, 9, 103),  -- Role type
    ('entry-001', 'attr-006', 1026, 10, 116), -- Array String type
    ('entry-001', 'attr-007', 4, 15, 200),    -- Text type
    ('entry-001', 'attr-008', 8, 16, 219),    -- Boolean type
    ('entry-001', 'attr-009', 32, 17, 234),   -- Date type
    ('entry-001', 'attr-010', 128, 18, 245),  -- DateTime type

    -- For entry-002 (similar pattern)
    ('entry-002', 'attr-011', 2, 5, 41),
    ('entry-002', 'attr-012', 1, 6, 57);
