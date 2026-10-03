import { EntryAttributeTypeTypeEnum } from "@dmm-com/airone-apiclient-typescript-fetch";

import { Schema, schema } from "./TriggerFormSchema";

import { ACLType } from "services/ACLUtil";

describe("schema", () => {
  // A valid value
  const baseValue: Schema = {
    id: 1,
    entity: {
      id: 1,
      name: "entity1",
      isPublic: true,
      permission: ACLType.Full,
    },
    conditions: [
      {
        id: 1,
        attr: {
          id: 1,
          name: "attr1",
          type: EntryAttributeTypeTypeEnum.STRING,
        },
        strCond: "str cond",
        refCond: null,
      },
    ],
    actions: [
      {
        id: 1,
        attr: {
          id: 1,
          name: "attr1",
          type: EntryAttributeTypeTypeEnum.STRING,
        },
        values: [
          {
            id: 1,
            strCond: "str cond",
            refCond: null,
          },
        ],
      },
    ],
  };

  test("validation succeeds for a valid value", () => {
    const value = { ...baseValue };
    expect(schema.parse(value)).toEqual(value);
  });

  test("validation fails if it does not have an entity", () => {
    const value = {
      ...baseValue,
      entity: undefined,
    };

    expect(() => schema.parse(value)).toThrow();
  });

  test("validation fails if it does not have conditions", () => {
    const value = {
      ...baseValue,
      conditions: [],
    };

    expect(() => schema.parse(value)).toThrow();
  });

  test("validation fails if it has a condition without an attr", () => {
    const value = {
      ...baseValue,
      conditions: [
        {
          ...baseValue.conditions[0],
          attr: undefined,
        },
      ],
    };

    expect(() => schema.parse(value)).toThrow();
  });

  test("validation fails if it does not have actions", () => {
    const value = {
      ...baseValue,
      actions: [],
    };

    expect(() => schema.parse(value)).toThrow();
  });

  test("validation fails if it has an action without an attr", () => {
    const value = {
      ...baseValue,
      actions: [
        {
          ...baseValue.actions[0],
          attr: undefined,
        },
      ],
    };

    expect(() => schema.parse(value)).toThrow();
  });

  test("validation fails with Japanese messages by default", () => {
    const result = schema.safeParse({
      ...baseValue,
      entity: { ...baseValue.entity, id: 0 },
      conditions: [],
    });
    expect(result.success).toBe(false);
    const messages = result.error?.issues.map(
      (issue: { message: string }) => issue.message,
    );
    expect(messages).toContain("モデルは必須です");
    expect(messages).toContain("最低でもひとつの条件を設定してください");
  });

  test("validation fails with English messages when language is English", async () => {
    vi.resetModules();
    const { default: i18n } = await import("i18n/config");
    await i18n.changeLanguage("en");
    const { schema } = await import("./TriggerFormSchema");
    const result = schema.safeParse({
      ...baseValue,
      entity: { ...baseValue.entity, id: 0 },
      conditions: [],
    });
    expect(result.success).toBe(false);
    const messages = result.error?.issues.map(
      (issue: { message: string }) => issue.message,
    );
    expect(messages).toContain("Model is required");
    expect(messages).toContain("Set at least one condition");

    // restore for later tests in the file
    vi.resetModules();
  });
});
