import { Schema, schema } from "./GroupFormSchema";

describe("schema", () => {
  // A valid value
  const baseValue: Schema = {
    id: 1,
    name: "group1",
    parentGroup: 100,
    members: [],
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

describe("schema messages", () => {
  const baseValue: Schema = {
    id: 1,
    name: "group1",
    parentGroup: 100,
    members: [],
  };

  test("japanese validation messages", () => {
    const result = schema.safeParse({ ...baseValue, name: "" });
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error.issues[0].message).toBe("グループ名は必須です");
    }
  });

  test("english validation messages", async () => {
    vi.resetModules();
    const { default: i18n } = await import("i18n/config");
    await i18n.changeLanguage("en");
    const { schema } = await import("./GroupFormSchema");
    const result = schema.safeParse({ ...baseValue, name: "" });
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error.issues[0].message).toBe("Group name is required");
    }
    // restore for later tests in the file
    vi.resetModules();
  });
});
