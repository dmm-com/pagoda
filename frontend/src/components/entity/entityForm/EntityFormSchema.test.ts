/**
 * @jest-environment jsdom
 */

import { z } from "zod";

import { AttributeTypes } from "../../../services/Constants";

import { Schema, schema } from "./EntityFormSchema";

describe("schema", () => {
  const baseValue: Schema = {
    name: "entity",
    note: "note",
    itemNamePattern: "",
    isToplevel: false,
    webhooks: [
      {
        url: "https://example.com/",
        label: "label",
        isEnabled: false,
        isVerified: false,
        headers: [
          {
            headerKey: "key1",
            headerValue: "value1",
          },
        ],
      },
    ],
    attrs: [
      {
        name: "attr1",
        type: AttributeTypes.string.type,
        isMandatory: false,
        isDeleteInChain: false,
        isSummarized: false,
        isWritable: true,
        referral: [
          {
            id: 1,
            name: "referred1",
          },
        ],
        note: "note",
        nameOrder: "0",
        namePrefix: "",
        namePostfix: "",
      },
    ],
  };

  test("validation succeeds for a valid value", () => {
    const value = { ...baseValue };
    expect(schema.parse(value)).toEqual(value);
  });

  test("validation fails if name is empty", () => {
    const value = {
      ...baseValue,
      name: "",
    };

    expect(() => schema.parse(value)).toThrow();
  });

  test("validation fails if webhook url is invalid format", () => {
    const value = {
      ...baseValue,
      webhooks: [
        {
          ...baseValue.webhooks[0],
          url: "invalid url",
        },
      ],
    };

    expect(() => schema.parse(value)).toThrow();
  });

  test("validation fails if webhook headers headerKey is empty", () => {
    const value = {
      ...baseValue,
      webhooks: [
        {
          ...baseValue.webhooks[0],
          headers: [
            {
              ...baseValue.webhooks[0].headers[0],
              headerKey: "",
            },
          ],
        },
      ],
    };

    expect(() => schema.parse(value)).toThrow();
  });

  test("validation fails if attr name is empty", () => {
    const value = {
      ...baseValue,
      attrs: [
        {
          ...baseValue.attrs[0],
          name: "",
        },
      ],
    };

    expect(() => schema.parse(value)).toThrow();
  });

  // Object-like types require a referral
  const objectLikeTestCases = [
    { type: AttributeTypes.object.type, name: "object" },
    { type: AttributeTypes.named_object.type, name: "named_object" },
    { type: AttributeTypes.array_object.type, name: "array_object" },
    {
      type: AttributeTypes.array_named_object.type,
      name: "array_named_object",
    },
  ];

  objectLikeTestCases.forEach(({ type, name }) => {
    test(`validation fails if ${name} type has empty referral`, () => {
      const value = {
        ...baseValue,
        attrs: [
          {
            ...baseValue.attrs[0],
            type: type,
            referral: [],
          },
        ],
      };

      expect(() => schema.parse(value)).toThrow();
    });

    test(`validation succeeds if ${name} type has non-empty referral`, () => {
      const value = {
        ...baseValue,
        attrs: [
          {
            ...baseValue.attrs[0],
            type: type,
            referral: [
              {
                id: 1,
                name: "referred1",
              },
            ],
          },
        ],
      };

      expect(schema.parse(value)).toEqual(value);
    });
  });

  // Non-object-like types do not require a referral
  const nonObjectLikeTestCases = [
    AttributeTypes.string.type,
    AttributeTypes.group.type,
    AttributeTypes.role.type,
    AttributeTypes.text.type,
    AttributeTypes.boolean.type,
    AttributeTypes.date.type,
    AttributeTypes.datetime.type,
    AttributeTypes.array_string.type,
    AttributeTypes.array_group.type,
    AttributeTypes.array_role.type,
  ];

  nonObjectLikeTestCases.forEach((type) => {
    test("validation succeeds if non-object-like type has empty referral", () => {
      const value = {
        ...baseValue,
        attrs: [
          {
            ...baseValue.attrs[0],
            type: type,
            referral: [],
          },
        ],
      };

      expect(schema.parse(value)).toEqual(value);
    });
  });

  describe("attribute name duplication", () => {
    const baseAttr = {
      // name: "attr1", // name will be set per test case
      type: AttributeTypes.string.type,
      isMandatory: false,
      isDeleteInChain: false,
      isSummarized: false,
      isWritable: true,
      referral: [],
      note: "note",
      nameOrder: "0",
      namePrefix: "",
      namePostfix: "",
    };

    test("validation succeeds if attribute names are unique", () => {
      const value: Schema = {
        ...baseValue,
        attrs: [
          { ...baseAttr, name: "attr1" },
          { ...baseAttr, name: "attr2" },
          { ...baseAttr, name: "attr3" },
        ],
      };
      const result = schema.safeParse(value);
      expect(result.success).toBe(true);
    });

    test("validation fails if two attribute names are duplicated", () => {
      const value: Schema = {
        ...baseValue,
        attrs: [
          { ...baseAttr, name: "attr1" },
          { ...baseAttr, name: "attr2" },
          { ...baseAttr, name: "attr1" },
        ],
      };
      const result = schema.safeParse(value);
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.issues).toEqual(
          expect.arrayContaining([
            expect.objectContaining({
              code: z.ZodIssueCode.custom,
              message: "属性名が重複しています",
              path: ["attrs", 0, "name"],
            }),
            expect.objectContaining({
              code: z.ZodIssueCode.custom,
              message: "属性名が重複しています",
              path: ["attrs", 2, "name"],
            }),
          ]),
        );
        // Ensure only duplication errors are present for this specific test's focus
        const duplicationIssues = result.error.issues.filter(
          (issue) => issue.message === "属性名が重複しています",
        );
        expect(duplicationIssues.length).toBe(2);
      }
    });

    test("validation fails if three attribute names are duplicated", () => {
      const value: Schema = {
        ...baseValue,
        attrs: [
          { ...baseAttr, name: "attr1" },
          { ...baseAttr, name: "attr2" },
          { ...baseAttr, name: "attr1" },
          { ...baseAttr, name: "attr1" },
        ],
      };
      const result = schema.safeParse(value);
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.issues).toEqual(
          expect.arrayContaining([
            expect.objectContaining({
              code: z.ZodIssueCode.custom,
              message: "属性名が重複しています",
              path: ["attrs", 0, "name"],
            }),
            expect.objectContaining({
              code: z.ZodIssueCode.custom,
              message: "属性名が重複しています",
              path: ["attrs", 2, "name"],
            }),
            expect.objectContaining({
              code: z.ZodIssueCode.custom,
              message: "属性名が重複しています",
              path: ["attrs", 3, "name"],
            }),
          ]),
        );
        const duplicationIssues = result.error.issues.filter(
          (issue) => issue.message === "属性名が重複しています",
        );
        expect(duplicationIssues.length).toBe(3);
      }
    });

    test("validation fails for multiple pairs of duplicated attribute names", () => {
      const value: Schema = {
        ...baseValue,
        attrs: [
          { ...baseAttr, name: "attr1" }, // dup with index 2
          { ...baseAttr, name: "attr2" }, // dup with index 4
          { ...baseAttr, name: "attr1" }, // dup with index 0
          { ...baseAttr, name: "attr3" },
          { ...baseAttr, name: "attr2" }, // dup with index 1
        ],
      };
      const result = schema.safeParse(value);
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.issues).toEqual(
          expect.arrayContaining([
            expect.objectContaining({
              code: z.ZodIssueCode.custom,
              message: "属性名が重複しています",
              path: ["attrs", 0, "name"],
            }),
            expect.objectContaining({
              code: z.ZodIssueCode.custom,
              message: "属性名が重複しています",
              path: ["attrs", 1, "name"],
            }),
            expect.objectContaining({
              code: z.ZodIssueCode.custom,
              message: "属性名が重複しています",
              path: ["attrs", 2, "name"],
            }),
            expect.objectContaining({
              code: z.ZodIssueCode.custom,
              message: "属性名が重複しています",
              path: ["attrs", 4, "name"],
            }),
          ]),
        );
        const duplicationIssues = result.error.issues.filter(
          (issue) => issue.message === "属性名が重複しています",
        );
        expect(duplicationIssues.length).toBe(4);
      }
    });

    test("validation includes other errors when duplicated names are empty strings (min length and duplication)", () => {
      // Individual empty names are caught by z.string().min(1) on attr.name
      // The superRefine logic for duplication specifically skips empty names but still runs.
      // This test ensures superRefine correctly flags actual duplications alongside min length errors.
      const value: Schema = {
        ...baseValue,
        attrs: [
          { ...baseAttr, name: "attr1" },
          { ...baseAttr, name: "" }, // This will cause a min(1) error
          { ...baseAttr, name: "attr1" }, // This will cause a duplication error
          { ...baseAttr, name: "" }, // This will cause another min(1) error
        ],
      };
      const result = schema.safeParse(value);
      expect(result.success).toBe(false);
      if (!result.success) {
        // Check for duplication errors
        expect(result.error.issues).toEqual(
          expect.arrayContaining([
            expect.objectContaining({
              code: z.ZodIssueCode.custom,
              message: "属性名が重複しています",
              path: ["attrs", 0, "name"],
            }),
            expect.objectContaining({
              code: z.ZodIssueCode.custom,
              message: "属性名が重複しています",
              path: ["attrs", 2, "name"],
            }),
          ]),
        );
        // Check for min length errors
        expect(result.error.issues).toEqual(
          expect.arrayContaining([
            expect.objectContaining({
              code: z.ZodIssueCode.too_small,
              minimum: 1,
              type: "string",
              inclusive: true,
              path: ["attrs", 1, "name"],
            }),
            expect.objectContaining({
              code: z.ZodIssueCode.too_small,
              minimum: 1,
              type: "string",
              inclusive: true,
              path: ["attrs", 3, "name"],
            }),
          ]),
        );
        const duplicationIssues = result.error.issues.filter(
          (issue) => issue.message === "属性名が重複しています",
        );
        expect(duplicationIssues.length).toBe(2);

        const minLengthIssues = result.error.issues.filter(
          (issue) =>
            issue.code === z.ZodIssueCode.too_small &&
            issue.path[0] === "attrs" &&
            issue.path[2] === "name",
        );
        expect(minLengthIssues.length).toBe(2);
      }
    });
  });
});
