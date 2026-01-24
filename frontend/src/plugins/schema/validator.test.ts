import { z } from "zod";

import { baseEntitySchema, requireAttr, requireReferral } from "./helpers";
import { AttrType, EntityStructure } from "./types";
import {
  createValidationErrorReport,
  formatValidationErrors,
  validateEntityStructure,
} from "./validator";

describe("validateEntityStructure", () => {
  // Sample entity that meets basic requirements
  const validEntity: EntityStructure = {
    id: 1,
    name: "NetworkDevice",
    attrs: [
      {
        id: 101,
        name: "hostname",
        type: AttrType.STRING,
        isMandatory: true,
        referral: [],
      },
      {
        id: 102,
        name: "ip_address",
        type: AttrType.STRING,
        isMandatory: true,
        referral: [],
      },
      {
        id: 103,
        name: "location",
        type: AttrType.OBJECT,
        isMandatory: false,
        referral: [
          { id: 1, name: "Datacenter" },
          { id: 2, name: "Office" },
        ],
      },
    ],
  };

  describe("with baseEntitySchema (no custom refinements)", () => {
    it("should pass validation for any valid entity structure", () => {
      const result = validateEntityStructure(validEntity, baseEntitySchema);

      expect(result.success).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it("should pass validation for entity with no attributes", () => {
      const emptyAttrsEntity: EntityStructure = {
        id: 1,
        name: "EmptyEntity",
        attrs: [],
      };

      const result = validateEntityStructure(
        emptyAttrsEntity,
        baseEntitySchema,
      );

      expect(result.success).toBe(true);
      expect(result.errors).toHaveLength(0);
    });
  });

  describe("with requireAttr refinement", () => {
    const schemaRequiringHostname = baseEntitySchema.refine(
      (entity) => requireAttr("hostname", AttrType.STRING)(entity.attrs),
      { message: 'Required attribute "hostname" (STRING) is missing' },
    );

    it("should pass when required attribute exists with correct type", () => {
      const result = validateEntityStructure(
        validEntity,
        schemaRequiringHostname,
      );

      expect(result.success).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it("should fail when required attribute is missing", () => {
      const entityWithoutHostname: EntityStructure = {
        id: 1,
        name: "TestEntity",
        attrs: [
          {
            id: 102,
            name: "ip_address",
            type: AttrType.STRING,
            isMandatory: true,
            referral: [],
          },
        ],
      };

      const result = validateEntityStructure(
        entityWithoutHostname,
        schemaRequiringHostname,
      );

      expect(result.success).toBe(false);
      expect(result.errors).toHaveLength(1);
      expect(result.errors[0].message).toBe(
        'Required attribute "hostname" (STRING) is missing',
      );
    });

    it("should fail when attribute exists but has wrong type", () => {
      const entityWithWrongType: EntityStructure = {
        id: 1,
        name: "TestEntity",
        attrs: [
          {
            id: 101,
            name: "hostname",
            type: AttrType.NUMBER, // Wrong type!
            isMandatory: true,
            referral: [],
          },
        ],
      };

      const result = validateEntityStructure(
        entityWithWrongType,
        schemaRequiringHostname,
      );

      expect(result.success).toBe(false);
      expect(result.errors).toHaveLength(1);
    });
  });

  describe("with multiple type options", () => {
    // Schema that accepts STRING or TEXT for description
    const schemaWithMultipleTypes = baseEntitySchema.refine(
      (entity) =>
        requireAttr("description", [AttrType.STRING, AttrType.TEXT])(
          entity.attrs,
        ),
      {
        message: 'Required attribute "description" (STRING or TEXT) is missing',
      },
    );

    it("should pass when attribute matches first type option", () => {
      const entity: EntityStructure = {
        id: 1,
        name: "Test",
        attrs: [
          {
            id: 1,
            name: "description",
            type: AttrType.STRING,
            isMandatory: false,
            referral: [],
          },
        ],
      };

      const result = validateEntityStructure(entity, schemaWithMultipleTypes);
      expect(result.success).toBe(true);
    });

    it("should pass when attribute matches second type option", () => {
      const entity: EntityStructure = {
        id: 1,
        name: "Test",
        attrs: [
          {
            id: 1,
            name: "description",
            type: AttrType.TEXT,
            isMandatory: false,
            referral: [],
          },
        ],
      };

      const result = validateEntityStructure(entity, schemaWithMultipleTypes);
      expect(result.success).toBe(true);
    });

    it("should fail when attribute type matches neither option", () => {
      const entity: EntityStructure = {
        id: 1,
        name: "Test",
        attrs: [
          {
            id: 1,
            name: "description",
            type: AttrType.NUMBER,
            isMandatory: false,
            referral: [],
          },
        ],
      };

      const result = validateEntityStructure(entity, schemaWithMultipleTypes);
      expect(result.success).toBe(false);
    });
  });

  describe("with requireReferral refinement", () => {
    const schemaRequiringReferral = baseEntitySchema
      .refine(
        (entity) => requireAttr("location", AttrType.OBJECT)(entity.attrs),
        { message: 'Required attribute "location" is missing' },
      )
      .refine(
        (entity) => requireReferral("location", ["Datacenter"])(entity.attrs),
        { message: 'Attribute "location" must reference Datacenter' },
      );

    it("should pass when referral entity exists", () => {
      const result = validateEntityStructure(
        validEntity,
        schemaRequiringReferral,
      );

      expect(result.success).toBe(true);
    });

    it("should fail when referral entity is missing", () => {
      const entityWithoutReferral: EntityStructure = {
        id: 1,
        name: "Test",
        attrs: [
          {
            id: 103,
            name: "location",
            type: AttrType.OBJECT,
            isMandatory: false,
            referral: [{ id: 99, name: "SomeOtherEntity" }],
          },
        ],
      };

      const result = validateEntityStructure(
        entityWithoutReferral,
        schemaRequiringReferral,
      );

      expect(result.success).toBe(false);
      expect(result.errors.some((e) => e.message.includes("Datacenter"))).toBe(
        true,
      );
    });

    it("should fail when attribute has no referrals", () => {
      const entityWithEmptyReferral: EntityStructure = {
        id: 1,
        name: "Test",
        attrs: [
          {
            id: 103,
            name: "location",
            type: AttrType.OBJECT,
            isMandatory: false,
            referral: [],
          },
        ],
      };

      const result = validateEntityStructure(
        entityWithEmptyReferral,
        schemaRequiringReferral,
      );

      expect(result.success).toBe(false);
    });
  });

  describe("with multiple refinements (chained)", () => {
    const strictSchema = baseEntitySchema
      .refine(
        (entity) => requireAttr("hostname", AttrType.STRING)(entity.attrs),
        { message: "hostname attribute is required" },
      )
      .refine(
        (entity) => requireAttr("ip_address", AttrType.STRING)(entity.attrs),
        { message: "ip_address attribute is required" },
      )
      .refine(
        (entity) => requireAttr("status", AttrType.STRING)(entity.attrs),
        { message: "status attribute is required" },
      );

    it("should pass when all requirements are met", () => {
      const entity: EntityStructure = {
        id: 1,
        name: "Test",
        attrs: [
          {
            id: 1,
            name: "hostname",
            type: AttrType.STRING,
            isMandatory: true,
            referral: [],
          },
          {
            id: 2,
            name: "ip_address",
            type: AttrType.STRING,
            isMandatory: true,
            referral: [],
          },
          {
            id: 3,
            name: "status",
            type: AttrType.STRING,
            isMandatory: false,
            referral: [],
          },
        ],
      };

      const result = validateEntityStructure(entity, strictSchema);
      expect(result.success).toBe(true);
    });

    it("should report first failing refinement", () => {
      // Zod reports the first failing refinement
      const entity: EntityStructure = {
        id: 1,
        name: "Test",
        attrs: [
          {
            id: 1,
            name: "hostname",
            type: AttrType.STRING,
            isMandatory: true,
            referral: [],
          },
          // Missing ip_address and status
        ],
      };

      const result = validateEntityStructure(entity, strictSchema);

      expect(result.success).toBe(false);
      expect(result.errors.length).toBeGreaterThanOrEqual(1);
      expect(result.errors[0].message).toBe("ip_address attribute is required");
    });
  });
});

describe("formatValidationErrors", () => {
  it("should format errors with path", () => {
    const errors: z.ZodIssue[] = [
      {
        code: "custom",
        path: ["attrs"],
        message: "hostname attribute is required",
      },
    ];

    const formatted = formatValidationErrors(errors);

    expect(formatted).toEqual(["attrs: hostname attribute is required"]);
  });

  it("should format errors without path", () => {
    const errors: z.ZodIssue[] = [
      {
        code: "custom",
        path: [],
        message: "Entity validation failed",
      },
    ];

    const formatted = formatValidationErrors(errors);

    expect(formatted).toEqual(["Entity validation failed"]);
  });

  it("should format multiple errors", () => {
    const errors: z.ZodIssue[] = [
      { code: "custom", path: ["attrs"], message: "Error 1" },
      { code: "custom", path: ["name"], message: "Error 2" },
      { code: "custom", path: [], message: "Error 3" },
    ];

    const formatted = formatValidationErrors(errors);

    expect(formatted).toHaveLength(3);
    expect(formatted[0]).toBe("attrs: Error 1");
    expect(formatted[1]).toBe("name: Error 2");
    expect(formatted[2]).toBe("Error 3");
  });

  it("should handle nested paths", () => {
    const errors: z.ZodIssue[] = [
      {
        code: "custom",
        path: ["attrs", 0, "referral"],
        message: "Invalid referral",
      },
    ];

    const formatted = formatValidationErrors(errors);

    expect(formatted).toEqual(["attrs.0.referral: Invalid referral"]);
  });
});

describe("createValidationErrorReport", () => {
  it("should create report with single error", () => {
    const errors: z.ZodIssue[] = [
      { code: "custom", path: ["attrs"], message: "Test error" },
    ];

    const report = createValidationErrorReport(errors);

    expect(report.summary).toBe("1 validation error found");
    expect(report.details).toHaveLength(1);
    expect(report.details[0]).toEqual({
      path: "attrs",
      message: "Test error",
      code: "custom",
    });
  });

  it("should create report with multiple errors", () => {
    const errors: z.ZodIssue[] = [
      { code: "custom", path: ["attrs"], message: "Error 1" },
      { code: "custom", path: ["name"], message: "Error 2" },
    ];

    const report = createValidationErrorReport(errors);

    expect(report.summary).toBe("2 validation errors found");
    expect(report.details).toHaveLength(2);
  });

  it("should use (root) for empty path", () => {
    const errors: z.ZodIssue[] = [
      { code: "custom", path: [], message: "Root error" },
    ];

    const report = createValidationErrorReport(errors);

    expect(report.details[0].path).toBe("(root)");
  });
});
