/**
 * @jest-environment jsdom
 */

import { DjangoContext } from "../../../services/DjangoContext";

import { schema, Schema } from "./EntryFormSchema";

describe("schema", () => {
  const djangoContext = DjangoContext.getInstance();

  const baseValue: Schema = {
    name: "entry",
    schema: {
      id: 2,
      name: "entity",
    },
    attrs: {
      string: {
        index: 0,
        type: djangoContext?.attrTypeValue.string ?? 0,
        isMandatory: false,
        schema: {
          id: 1,
          name: "string",
        },
        value: {
          asString: "string",
        },
      },
    },
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
});
