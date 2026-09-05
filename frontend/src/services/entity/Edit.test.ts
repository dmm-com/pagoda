import { describe, expect, test } from "vitest";

import { processAttrDefaultValue } from "./Edit";

import { BaseAttributeTypes } from "services/Constants";

describe("processAttrDefaultValue", () => {
  describe("number type", () => {
    const numberType = BaseAttributeTypes.number;

    test("converts numeric string to number", () => {
      expect(processAttrDefaultValue(numberType, "42")).toBe(42);
      expect(processAttrDefaultValue(numberType, "3.14")).toBe(3.14);
      expect(processAttrDefaultValue(numberType, -7)).toBe(-7);
    });

    test("converts emptied input to null (clear the default)", () => {
      // Number("") is 0, not NaN, so it must be handled explicitly
      expect(processAttrDefaultValue(numberType, "")).toBeNull();
      expect(processAttrDefaultValue(numberType, null)).toBeNull();
      expect(processAttrDefaultValue(numberType, undefined)).toBeNull();
    });

    test("converts non-numeric string to null", () => {
      expect(processAttrDefaultValue(numberType, "abc")).toBeNull();
    });
  });

  describe("string / text type", () => {
    const stringType = BaseAttributeTypes.string;
    const textType = BaseAttributeTypes.text;

    test("passes string through", () => {
      expect(processAttrDefaultValue(stringType, "foo")).toBe("foo");
      expect(processAttrDefaultValue(textType, "line1\nline2")).toBe(
        "line1\nline2",
      );
    });

    test("converts emptied input to null (clear the default)", () => {
      expect(processAttrDefaultValue(stringType, "")).toBeNull();
      expect(processAttrDefaultValue(textType, "")).toBeNull();
      expect(processAttrDefaultValue(stringType, null)).toBeNull();
    });
  });

  describe("boolean type", () => {
    const boolType = BaseAttributeTypes.bool;

    test("coerces to boolean", () => {
      expect(processAttrDefaultValue(boolType, true)).toBe(true);
      expect(processAttrDefaultValue(boolType, false)).toBe(false);
    });

    test("converts null to null", () => {
      expect(processAttrDefaultValue(boolType, null)).toBeNull();
    });
  });

  test("passes through value for unsupported types", () => {
    const objectType = BaseAttributeTypes.object;
    expect(processAttrDefaultValue(objectType, "foo")).toBe("foo");
    expect(processAttrDefaultValue(objectType, null)).toBeNull();
  });
});
