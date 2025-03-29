/**
 * @jest-environment jsdom
 */

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
  test("validation succeeds if non-object-like type has empty referral", () => {
    const value = {
      ...baseValue,
      attrs: [
        {
          ...baseValue.attrs[0],
          type: AttributeTypes.string.type,
          referral: [],
        },
      ],
    };

    expect(schema.parse(value)).toEqual(value);
  });
});
