import {
  requireAttr,
  requireReferral,
  missingAttrMessage,
  missingReferralMessage,
  createEntitySchema,
} from "./helpers";
import { EntityAttrStructure, AttrType } from "./types";

describe("requireAttr", () => {
  const sampleAttrs: EntityAttrStructure[] = [
    {
      id: 1,
      name: "hostname",
      type: AttrType.STRING,
      isMandatory: true,
      referral: [],
    },
    {
      id: 2,
      name: "port",
      type: AttrType.NUMBER,
      isMandatory: false,
      referral: [],
    },
    {
      id: 3,
      name: "tags",
      type: AttrType.ARRAY_STRING,
      isMandatory: false,
      referral: [],
    },
    {
      id: 4,
      name: "owner",
      type: AttrType.OBJECT,
      isMandatory: true,
      referral: [{ id: 10, name: "User" }],
    },
  ];

  describe("basic attribute matching", () => {
    it("should return true when attribute exists with matching type", () => {
      const check = requireAttr("hostname", AttrType.STRING);
      expect(check(sampleAttrs)).toBe(true);
    });

    it("should return false when attribute does not exist", () => {
      const check = requireAttr("nonexistent", AttrType.STRING);
      expect(check(sampleAttrs)).toBe(false);
    });

    it("should return false when attribute exists but type does not match", () => {
      const check = requireAttr("hostname", AttrType.NUMBER);
      expect(check(sampleAttrs)).toBe(false);
    });

    it("should return false for empty attrs array", () => {
      const check = requireAttr("hostname", AttrType.STRING);
      expect(check([])).toBe(false);
    });
  });

  describe("multiple type matching", () => {
    it("should return true when type matches one of multiple options", () => {
      const check = requireAttr("hostname", [AttrType.STRING, AttrType.TEXT]);
      expect(check(sampleAttrs)).toBe(true);
    });

    it("should return true when type matches second option", () => {
      const check = requireAttr("port", [AttrType.STRING, AttrType.NUMBER]);
      expect(check(sampleAttrs)).toBe(true);
    });

    it("should return false when type matches none of the options", () => {
      const check = requireAttr("hostname", [
        AttrType.NUMBER,
        AttrType.BOOLEAN,
      ]);
      expect(check(sampleAttrs)).toBe(false);
    });
  });

  describe("mustBeMandatory option", () => {
    it("should return true when attribute is mandatory and option is set", () => {
      const check = requireAttr("hostname", AttrType.STRING, {
        mustBeMandatory: true,
      });
      expect(check(sampleAttrs)).toBe(true);
    });

    it("should return false when attribute is not mandatory but option requires it", () => {
      const check = requireAttr("port", AttrType.NUMBER, {
        mustBeMandatory: true,
      });
      expect(check(sampleAttrs)).toBe(false);
    });

    it("should return true when attribute is not mandatory and option is not set", () => {
      const check = requireAttr("port", AttrType.NUMBER);
      expect(check(sampleAttrs)).toBe(true);
    });

    it("should return true when attribute is not mandatory and mustBeMandatory is false", () => {
      const check = requireAttr("port", AttrType.NUMBER, {
        mustBeMandatory: false,
      });
      expect(check(sampleAttrs)).toBe(true);
    });
  });

  describe("with various AttrType values", () => {
    it("should match ARRAY_STRING type", () => {
      const check = requireAttr("tags", AttrType.ARRAY_STRING);
      expect(check(sampleAttrs)).toBe(true);
    });

    it("should match OBJECT type", () => {
      const check = requireAttr("owner", AttrType.OBJECT);
      expect(check(sampleAttrs)).toBe(true);
    });

    it("should not match combined types incorrectly", () => {
      // ARRAY_STRING (1026) should not match STRING (2)
      const check = requireAttr("tags", AttrType.STRING);
      expect(check(sampleAttrs)).toBe(false);
    });
  });
});

describe("requireReferral", () => {
  const attrsWithReferrals: EntityAttrStructure[] = [
    {
      id: 1,
      name: "location",
      type: AttrType.OBJECT,
      isMandatory: false,
      referral: [
        { id: 10, name: "Datacenter" },
        { id: 11, name: "Office" },
        { id: 12, name: "Warehouse" },
      ],
    },
    {
      id: 2,
      name: "owner",
      type: AttrType.OBJECT,
      isMandatory: false,
      referral: [{ id: 20, name: "User" }],
    },
    {
      id: 3,
      name: "tags",
      type: AttrType.ARRAY_STRING,
      isMandatory: false,
      referral: [],
    },
  ];

  describe("requireAll mode (default)", () => {
    it("should return true when all required referrals exist", () => {
      const check = requireReferral("location", ["Datacenter", "Office"]);
      expect(check(attrsWithReferrals)).toBe(true);
    });

    it("should return true for single required referral", () => {
      const check = requireReferral("location", ["Datacenter"]);
      expect(check(attrsWithReferrals)).toBe(true);
    });

    it("should return false when one required referral is missing", () => {
      const check = requireReferral("location", ["Datacenter", "NonExistent"]);
      expect(check(attrsWithReferrals)).toBe(false);
    });

    it("should return false when all required referrals are missing", () => {
      const check = requireReferral("location", ["A", "B"]);
      expect(check(attrsWithReferrals)).toBe(false);
    });

    it("should return false when attribute does not exist", () => {
      const check = requireReferral("nonexistent", ["Datacenter"]);
      expect(check(attrsWithReferrals)).toBe(false);
    });

    it("should return false when attribute has no referrals", () => {
      const check = requireReferral("tags", ["SomeEntity"]);
      expect(check(attrsWithReferrals)).toBe(false);
    });
  });

  describe("requireAll: false mode (any match)", () => {
    it("should return true when at least one referral matches", () => {
      const check = requireReferral("location", ["Datacenter", "NonExistent"], {
        requireAll: false,
      });
      expect(check(attrsWithReferrals)).toBe(true);
    });

    it("should return false when no referrals match", () => {
      const check = requireReferral("location", ["A", "B"], {
        requireAll: false,
      });
      expect(check(attrsWithReferrals)).toBe(false);
    });
  });

  describe("edge cases", () => {
    it("should handle empty entityNames array", () => {
      const check = requireReferral("location", []);
      // every() on empty array returns true
      expect(check(attrsWithReferrals)).toBe(true);
    });

    it("should handle empty attrs array", () => {
      const check = requireReferral("location", ["Datacenter"]);
      expect(check([])).toBe(false);
    });
  });
});

describe("missingAttrMessage", () => {
  it("should generate message for single type", () => {
    const message = missingAttrMessage("hostname", AttrType.STRING);
    expect(message).toBe('Attribute "hostname" (String) is required');
  });

  it("should generate message for multiple types", () => {
    const message = missingAttrMessage("description", [
      AttrType.STRING,
      AttrType.TEXT,
    ]);
    expect(message).toBe('Attribute "description" (String/Text) is required');
  });

  it("should handle unknown type codes gracefully", () => {
    const message = missingAttrMessage("unknown", 99999);
    expect(message).toBe('Attribute "unknown" (type 99999) is required');
  });
});

describe("missingReferralMessage", () => {
  it("should generate message for single referral", () => {
    const message = missingReferralMessage("location", ["Datacenter"]);
    expect(message).toBe('Attribute "location" must reference: Datacenter');
  });

  it("should generate message for multiple referrals", () => {
    const message = missingReferralMessage("location", [
      "Datacenter",
      "Office",
    ]);
    expect(message).toBe(
      'Attribute "location" must reference: Datacenter, Office',
    );
  });
});

describe("createEntitySchema", () => {
  it("should create schema with single requirement", () => {
    const schema = createEntitySchema([
      { name: "hostname", type: AttrType.STRING },
    ]);

    const validEntity = {
      id: 1,
      name: "Test",
      attrs: [
        {
          id: 1,
          name: "hostname",
          type: AttrType.STRING,
          isMandatory: false,
          referral: [],
        },
      ],
    };

    const result = schema.safeParse(validEntity);
    expect(result.success).toBe(true);
  });

  it("should fail validation when requirement not met", () => {
    const schema = createEntitySchema([
      { name: "hostname", type: AttrType.STRING },
    ]);

    const invalidEntity = {
      id: 1,
      name: "Test",
      attrs: [],
    };

    const result = schema.safeParse(invalidEntity);
    expect(result.success).toBe(false);
  });

  it("should create schema with multiple requirements", () => {
    const schema = createEntitySchema([
      { name: "hostname", type: AttrType.STRING },
      { name: "port", type: AttrType.NUMBER },
    ]);

    const validEntity = {
      id: 1,
      name: "Test",
      attrs: [
        {
          id: 1,
          name: "hostname",
          type: AttrType.STRING,
          isMandatory: false,
          referral: [],
        },
        {
          id: 2,
          name: "port",
          type: AttrType.NUMBER,
          isMandatory: false,
          referral: [],
        },
      ],
    };

    const result = schema.safeParse(validEntity);
    expect(result.success).toBe(true);
  });

  it("should create schema with referral requirement", () => {
    const schema = createEntitySchema([
      {
        name: "location",
        type: AttrType.OBJECT,
        referrals: ["Datacenter"],
      },
    ]);

    const validEntity = {
      id: 1,
      name: "Test",
      attrs: [
        {
          id: 1,
          name: "location",
          type: AttrType.OBJECT,
          isMandatory: false,
          referral: [{ id: 10, name: "Datacenter" }],
        },
      ],
    };

    const result = schema.safeParse(validEntity);
    expect(result.success).toBe(true);
  });

  it("should fail when referral requirement not met", () => {
    const schema = createEntitySchema([
      {
        name: "location",
        type: AttrType.OBJECT,
        referrals: ["Datacenter"],
      },
    ]);

    const invalidEntity = {
      id: 1,
      name: "Test",
      attrs: [
        {
          id: 1,
          name: "location",
          type: AttrType.OBJECT,
          isMandatory: false,
          referral: [{ id: 10, name: "SomeOtherEntity" }],
        },
      ],
    };

    const result = schema.safeParse(invalidEntity);
    expect(result.success).toBe(false);
  });

  it("should use custom message when provided", () => {
    const customMessage = "カスタムエラーメッセージ";
    const schema = createEntitySchema([
      { name: "hostname", type: AttrType.STRING, message: customMessage },
    ]);

    const invalidEntity = {
      id: 1,
      name: "Test",
      attrs: [],
    };

    const result = schema.safeParse(invalidEntity);
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error.issues[0].message).toBe(customMessage);
    }
  });

  it("should handle mustBeMandatory option", () => {
    const schema = createEntitySchema([
      { name: "hostname", type: AttrType.STRING, mustBeMandatory: true },
    ]);

    const entityWithOptionalAttr = {
      id: 1,
      name: "Test",
      attrs: [
        {
          id: 1,
          name: "hostname",
          type: AttrType.STRING,
          isMandatory: false, // Not mandatory!
          referral: [],
        },
      ],
    };

    const result = schema.safeParse(entityWithOptionalAttr);
    expect(result.success).toBe(false);
  });

  it("should return valid schema for empty requirements", () => {
    const schema = createEntitySchema([]);

    const anyEntity = {
      id: 1,
      name: "Test",
      attrs: [],
    };

    const result = schema.safeParse(anyEntity);
    expect(result.success).toBe(true);
  });
});
