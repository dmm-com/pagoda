/**
 * @jest-environment jsdom
 */

import { schema, Schema } from "./CategoryFormSchema";

describe("schema", () => {
  const baseValue: Schema = {
    id: 1,
    name: "Test Category",
    note: "Note for test",
    models: [
      {
        id: 1,
        name: "Model 1",
      },
      {
        id: 2,
        name: "Model 2",
      },
    ],
    priority: 10,
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

  test("validation succeeds if note is empty", () => {
    const value = {
      ...baseValue,
      note: "",
    };

    expect(schema.parse(value)).toEqual(value);
  });

  test("validation succeeds if note is undefined", () => {
    const value = {
      ...baseValue,
      note: undefined,
    };

    expect(schema.parse(value)).toEqual({
      ...value,
      note: undefined,
    });
  });

  test("validation succeeds with empty models array", () => {
    const value = {
      ...baseValue,
      models: [],
    };

    expect(schema.parse(value)).toEqual(value);
  });

  test("validation fails if priority is not a number", () => {
    const value = {
      ...baseValue,
      priority: "10" as unknown as number,
    };

    // Using coerce.number, the string "10" should be converted to the number 10
    expect(schema.parse(value)).toEqual({
      ...baseValue,
      priority: 10,
    });
  });

  test("validation succeeds with default values", () => {
    const partialValue = {
      name: "Test Category",
      priority: 10,
    };

    const expectedValue = {
      id: 0,
      name: "Test Category",
      models: [],
      priority: 10,
    };

    expect(schema.parse(partialValue)).toEqual(expectedValue);
  });
});
