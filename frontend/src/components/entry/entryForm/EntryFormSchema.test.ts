/**
 * @jest-environment jsdom
 */

import { EntryAttributeTypeTypeEnum } from "@dmm-com/airone-apiclient-typescript-fetch";

import { schema, Schema } from "./EntryFormSchema";

describe("schema", () => {
  const baseValue: Schema = {
    name: "entry",
    schema: {
      id: 2,
      name: "entity",
    },
    attrs: {
      string: {
        type: EntryAttributeTypeTypeEnum.STRING,
        index: 0,
        isMandatory: false,
        schema: {
          id: 1,
          name: "string",
        },
        value: {
          asString: "string",
        },
      },
      arrayString: {
        type: EntryAttributeTypeTypeEnum.ARRAY_STRING,
        index: 1,
        isMandatory: false,
        schema: {
          id: 1,
          name: "array_string",
        },
        value: {
          asArrayString: [{ value: "string" }],
        },
      },
      object: {
        type: EntryAttributeTypeTypeEnum.OBJECT,
        index: 2,
        isMandatory: false,
        schema: {
          id: 1,
          name: "object",
        },
        value: {
          asObject: {
            id: 1,
            name: "object",
          },
        },
      },
      arrayObject: {
        type: EntryAttributeTypeTypeEnum.ARRAY_OBJECT,
        index: 3,
        isMandatory: false,
        schema: {
          id: 1,
          name: "array_object",
        },
        value: {
          asArrayObject: [
            {
              id: 1,
              name: "object",
            },
          ],
        },
      },
      namedObject: {
        type: EntryAttributeTypeTypeEnum.NAMED_OBJECT,
        index: 4,
        isMandatory: false,
        schema: {
          id: 1,
          name: "named_object",
        },
        value: {
          asNamedObject: {
            name: "name",
            object: {
              id: 1,
              name: "object",
            },
          },
        },
      },
      arrayNamedObject: {
        type: EntryAttributeTypeTypeEnum.ARRAY_NAMED_OBJECT,
        index: 5,
        isMandatory: false,
        schema: {
          id: 1,
          name: "array_named_object",
        },
        value: {
          asArrayNamedObject: [
            {
              name: "name",
              object: {
                id: 1,
                name: "object",
              },
              _boolean: false,
            },
          ],
        },
      },
      group: {
        type: EntryAttributeTypeTypeEnum.GROUP,
        index: 6,
        isMandatory: false,
        schema: {
          id: 1,
          name: "group",
        },
        value: {
          asGroup: {
            id: 1,
            name: "group",
          },
        },
      },
      arrayGroup: {
        type: EntryAttributeTypeTypeEnum.ARRAY_GROUP,
        index: 7,
        isMandatory: false,
        schema: {
          id: 1,
          name: "array_group",
        },
        value: {
          asArrayGroup: [
            {
              id: 1,
              name: "group",
            },
          ],
        },
      },
      role: {
        type: EntryAttributeTypeTypeEnum.ROLE,
        index: 8,
        isMandatory: false,
        schema: {
          id: 1,
          name: "role",
        },
        value: {
          asRole: {
            id: 1,
            name: "role",
          },
        },
      },
      arrayRole: {
        type: EntryAttributeTypeTypeEnum.ARRAY_ROLE,
        index: 9,
        isMandatory: false,
        schema: {
          id: 1,
          name: "role",
        },
        value: {
          asArrayRole: [
            {
              id: 1,
              name: "role",
            },
          ],
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

  test("validation fails if name is too large", () => {
    const value = {
      ...baseValue,
      name: "x".repeat(201),
    };

    expect(() => schema.parse(value)).toThrow();
  });

  test("validation fails if name has only whitespaces", () => {
    const value = {
      ...baseValue,
      name: "   ",
    };

    expect(() => schema.parse(value)).toThrow();
  });

  test("validation fails if string attr value is mandatory and empty", () => {
    const value = {
      ...baseValue,
      attrs: {
        string: {
          ...baseValue.attrs.string,
          isMandatory: true,
          value: {
            asString: "",
          },
        },
      },
    };

    expect(() => schema.parse(value)).toThrow();
  });

  test("validation fails if string attr value is too large", () => {
    const value = {
      ...baseValue,
      attrs: {
        string: {
          ...baseValue.attrs.string,
          value: {
            asString: "a".repeat((1 << 16) + 1),
          },
        },
      },
    };

    expect(() => schema.parse(value)).toThrow();
  });

  test("validation fails if array-string attr value is mandatory and empty", () => {
    const value = {
      ...baseValue,
      attrs: {
        arrayString: {
          ...baseValue.attrs.arrayString,
          isMandatory: true,
          value: {
            asArrayString: [],
          },
        },
      },
    };

    expect(() => schema.parse(value)).toThrow();
  });

  test("validation fails if array-string attr value has an element is too large", () => {
    const value = {
      ...baseValue,
      attrs: {
        arrayString: {
          ...baseValue.attrs.arrayString,
          value: {
            asArrayString: ["a".repeat((1 << 16) + 1)],
          },
        },
      },
    };

    expect(() => schema.parse(value)).toThrow();
  });

  test("validation fails if object attr value is mandatory and empty", () => {
    const value = {
      ...baseValue,
      attrs: {
        object: {
          ...baseValue.attrs.object,
          isMandatory: true,
          value: {
            asObject: null,
          },
        },
      },
    };

    expect(() => schema.parse(value)).toThrow();
  });

  test("validation fails if array-object attr value is mandatory and empty", () => {
    const value = {
      ...baseValue,
      attrs: {
        object: {
          ...baseValue.attrs.object,
          isMandatory: true,
          value: {
            asArrayObject: [null],
          },
        },
      },
    };

    expect(() => schema.parse(value)).toThrow();
  });

  test("validation fails if named-object attr value is mandatory and empty", () => {
    const value = {
      ...baseValue,
      attrs: {
        namedObject: {
          ...baseValue.attrs.namedObject,
          isMandatory: true,
          value: {
            asNamedObject: { name: null },
          },
        },
      },
    };

    expect(() => schema.parse(value)).toThrow();
  });

  test("validation fails if array-named-object attr value is mandatory and empty", () => {
    const value = {
      ...baseValue,
      attrs: {
        arrayNamedObject: {
          ...baseValue.attrs.arrayNamedObject,
          isMandatory: true,
          value: {
            asArrayNamedObject: [{ name: null }],
          },
        },
      },
    };

    expect(() => schema.parse(value)).toThrow();
  });

  test("validation fails if group attr value is mandatory and empty", () => {
    const value = {
      ...baseValue,
      attrs: {
        group: {
          ...baseValue.attrs.group,
          isMandatory: true,
          value: {
            asGroup: null,
          },
        },
      },
    };

    expect(() => schema.parse(value)).toThrow();
  });

  test("validation fails if array-group attr value is mandatory and empty", () => {
    const value = {
      ...baseValue,
      attrs: {
        arrayGroup: {
          ...baseValue.attrs.arrayGroup,
          isMandatory: true,
          value: {
            asArrayGroup: [null],
          },
        },
      },
    };

    expect(() => schema.parse(value)).toThrow();
  });

  test("validation fails if role attr value is mandatory and empty", () => {
    const value = {
      ...baseValue,
      attrs: {
        role: {
          ...baseValue.attrs.role,
          isMandatory: true,
          value: {
            asRole: null,
          },
        },
      },
    };

    expect(() => schema.parse(value)).toThrow();
  });

  test("validation fails if array-role attr value is mandatory and empty", () => {
    const value = {
      ...baseValue,
      attrs: {
        arrayRole: {
          ...baseValue.attrs.arrayRole,
          isMandatory: true,
          value: {
            asArrayRole: [null],
          },
        },
      },
    };

    expect(() => schema.parse(value)).toThrow();
  });
});
