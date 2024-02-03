import { EntryAttributeTypeTypeEnum } from "@dmm-com/airone-apiclient-typescript-fetch";

import { Schema, schema } from "./TriggerFormSchema";

describe("schema", () => {
  // A valid value
  const baseValue: Schema = {
    id: 1,
    entity: {
      id: 1,
      name: "entity1",
      isPublic: true,
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
});
