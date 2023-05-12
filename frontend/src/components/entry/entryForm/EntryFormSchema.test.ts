/**
 * @jest-environment jsdom
 */

import { AttributeTypes } from "../../../services/Constants";

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
        type: AttributeTypes.string.type,
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
        type: AttributeTypes.array_string.type,
        index: 1,
        isMandatory: false,
        schema: {
          id: 1,
          name: "array_string",
        },
        value: {
          asArrayString: ["string"],
        },
      },
      object: {
        type: AttributeTypes.object.type,
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
            _boolean: false,
          },
        },
      },
      arrayObject: {
        type: AttributeTypes.array_object.type,
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
              _boolean: false,
            },
          ],
        },
      },
      namedObject: {
        type: AttributeTypes.named_object.type,
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
              _boolean: false,
            },
          },
        },
      },
      arrayNamedObject: {
        type: AttributeTypes.array_named_object.type,
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
                _boolean: false,
              },
            },
          ],
        },
      },
      group: {
        type: AttributeTypes.group.type,
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
        type: AttributeTypes.array_group.type,
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
        type: AttributeTypes.role.type,
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
        type: AttributeTypes.array_role.type,
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
