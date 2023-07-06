/**
 * @jest-environment jsdom
 */

import { AttributeTypes } from "../../../services/Constants";

import { Schema, schema } from "./EntityFormSchema";

describe("schema", () => {
  const baseValue: Schema = {
    name: "entity",
    note: "note",
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
});
