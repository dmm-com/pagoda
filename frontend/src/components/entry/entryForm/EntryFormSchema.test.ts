/**
 * @jest-environment jsdom
 */

import { schema, Schema } from "./EntryFormSchema";

import { EntryAttributeTypeTypeEnum } from "@dmm-com/airone-apiclient-typescript-fetch";

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
      number: {
        type: EntryAttributeTypeTypeEnum.NUMBER,
        index: 10,
        isMandatory: false,
        schema: {
          id: 1,
          name: "number",
        },
        value: {
          asNumber: 42,
        },
      },
      arrayNumber: {
        type: EntryAttributeTypeTypeEnum.ARRAY_NUMBER,
        index: 11,
        isMandatory: false,
        schema: {
          id: 1,
          name: "array_number",
        },
        value: {
          asArrayNumber: [
            {
              value: 123,
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

  test("validation fails if string-like attr value is mandatory and empty", () => {
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

    [
      EntryAttributeTypeTypeEnum.STRING,
      EntryAttributeTypeTypeEnum.TEXT,
      EntryAttributeTypeTypeEnum.DATE,
      EntryAttributeTypeTypeEnum.DATETIME,
    ].forEach((type) => {
      expect(() => schema.parse({ ...value, type })).toThrow();
    });
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

  test("validation fails if name contains 4-byte characters", () => {
    const value = {
      ...baseValue,
      name: "テスト😊", // Contains emoji (4-byte character)
    };

    expect(() => schema.parse(value)).toThrow();
  });

  test("validation fails if string attribute value contains 4-byte characters", () => {
    const value = {
      ...baseValue,
      attrs: {
        string: {
          ...baseValue.attrs.string,
          value: {
            asString: "テスト🚀", // Contains emoji (4-byte character)
          },
        },
      },
    };

    expect(() => schema.parse(value)).toThrow();
  });

  test("validation fails if array string attribute value contains 4-byte characters", () => {
    const value = {
      ...baseValue,
      attrs: {
        arrayString: {
          ...baseValue.attrs.arrayString,
          value: {
            asArrayString: [{ value: "テスト🎮" }], // Contains emoji (4-byte character)
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

  test("validation fails if date/datetime attr value is non-empty and invalid", () => {
    const value = {
      ...baseValue,
      attrs: {
        string: {
          ...baseValue.attrs.string,
          type: EntryAttributeTypeTypeEnum.DATETIME,
          isMandatory: true,
          value: {
            asString: "invalid date",
          },
        },
      },
    };

    [
      EntryAttributeTypeTypeEnum.DATE,
      EntryAttributeTypeTypeEnum.DATETIME,
    ].forEach((type) => {
      expect(() => schema.parse({ ...value, type })).toThrow();
    });
  });

  test("validation succeeds for valid number values", () => {
    const testCases = [
      { value: 0 },
      { value: 42 },
      { value: -123 },
      { value: 123.45 },
      { value: -456.789 },
      { value: null }, // null is allowed for non-mandatory fields
    ];

    testCases.forEach(({ value: numberValue }) => {
      const value = {
        ...baseValue,
        attrs: {
          number: {
            ...baseValue.attrs.number,
            value: {
              asNumber: numberValue,
            },
          },
        },
      };

      expect(() => schema.parse(value)).not.toThrow();
    });
  });

  test("validation fails if number attr value is mandatory and null", () => {
    const value = {
      ...baseValue,
      attrs: {
        number: {
          ...baseValue.attrs.number,
          isMandatory: true,
          value: {
            asNumber: null,
          },
        },
      },
    };

    expect(() => schema.parse(value)).toThrow();
  });

  test("validation succeeds for valid array-number values", () => {
    const testCases = [
      { value: [] }, // empty array for non-mandatory
      { value: [{ value: 0 }] },
      { value: [{ value: 42 }, { value: -123 }] },
      { value: [{ value: 123.45 }, { value: -456.789 }] },
      { value: [{ value: null }] }, // null values are allowed in array elements
      { value: [{ value: 1 }, { value: null }, { value: 3 }] },
    ];

    testCases.forEach(({ value: arrayValue }) => {
      const value = {
        ...baseValue,
        attrs: {
          arrayNumber: {
            ...baseValue.attrs.arrayNumber,
            value: {
              asArrayNumber: arrayValue,
            },
          },
        },
      };

      expect(() => schema.parse(value)).not.toThrow();
    });
  });

  test("validation fails if array-number attr value is mandatory and empty", () => {
    const value = {
      ...baseValue,
      attrs: {
        arrayNumber: {
          ...baseValue.attrs.arrayNumber,
          isMandatory: true,
          value: {
            asArrayNumber: [],
          },
        },
      },
    };

    expect(() => schema.parse(value)).toThrow();
  });

  test("validation fails if array-number attr value is mandatory and contains only null values", () => {
    const value = {
      ...baseValue,
      attrs: {
        arrayNumber: {
          ...baseValue.attrs.arrayNumber,
          isMandatory: true,
          value: {
            asArrayNumber: [{ value: null }],
          },
        },
      },
    };

    expect(() => schema.parse(value)).toThrow();
  });

  test("validation succeeds if array-number attr value is mandatory and contains at least one non-null value", () => {
    const value = {
      ...baseValue,
      attrs: {
        arrayNumber: {
          ...baseValue.attrs.arrayNumber,
          isMandatory: true,
          value: {
            asArrayNumber: [{ value: null }, { value: 42 }, { value: null }],
          },
        },
      },
    };

    expect(() => schema.parse(value)).not.toThrow();
  });

  test("validation handles extreme number values", () => {
    const testCases = [
      { value: Number.MAX_SAFE_INTEGER },
      { value: Number.MIN_SAFE_INTEGER },
      { value: 1e10 },
      { value: -1e10 },
      { value: 0.000001 },
      { value: -0.000001 },
    ];

    testCases.forEach(({ value: numberValue }) => {
      const value = {
        ...baseValue,
        attrs: {
          number: {
            ...baseValue.attrs.number,
            value: {
              asNumber: numberValue,
            },
          },
        },
      };

      expect(() => schema.parse(value)).not.toThrow();
    });
  });

  describe("mandatory field validation error paths", () => {
    test("string mandatory field error has correct path", () => {
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

      const result = schema.safeParse(value);
      expect(result.success).toBe(false);
      if (!result.success) {
        const error = result.error.issues.find(
          (issue) =>
            issue.path.join(".") === "attrs.string.value.asString" &&
            issue.message === "必須項目です",
        );
        expect(error).toBeDefined();
      }
    });

    test("array string mandatory field error has correct path", () => {
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

      const result = schema.safeParse(value);
      expect(result.success).toBe(false);
      if (!result.success) {
        const error = result.error.issues.find(
          (issue) =>
            issue.path.join(".") ===
              "attrs.arrayString.value.asArrayString.0.value" &&
            issue.message === "必須項目です",
        );
        expect(error).toBeDefined();
      }
    });

    test("object mandatory field error has correct path", () => {
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

      const result = schema.safeParse(value);
      expect(result.success).toBe(false);
      if (!result.success) {
        const error = result.error.issues.find(
          (issue) =>
            issue.path.join(".") === "attrs.object.value.asObject" &&
            issue.message === "必須項目です",
        );
        expect(error).toBeDefined();
      }
    });

    test("named object mandatory field error has correct paths", () => {
      const value = {
        ...baseValue,
        attrs: {
          namedObject: {
            ...baseValue.attrs.namedObject,
            isMandatory: true,
            value: {
              asNamedObject: {
                name: "",
                object: null,
              },
            },
          },
        },
      };

      const result = schema.safeParse(value);
      expect(result.success).toBe(false);
      if (!result.success) {
        const nameError = result.error.issues.find(
          (issue) =>
            issue.path.join(".") ===
              "attrs.namedObject.value.asNamedObject.name" &&
            issue.message === "必須項目です",
        );
        const objectError = result.error.issues.find(
          (issue) =>
            issue.path.join(".") ===
              "attrs.namedObject.value.asNamedObject.object" &&
            issue.message === "必須項目です",
        );
        expect(nameError).toBeDefined();
        expect(objectError).toBeDefined();
      }
    });

    test("array named object mandatory field error has correct paths", () => {
      const value = {
        ...baseValue,
        attrs: {
          arrayNamedObject: {
            ...baseValue.attrs.arrayNamedObject,
            isMandatory: true,
            value: {
              asArrayNamedObject: [],
            },
          },
        },
      };

      const result = schema.safeParse(value);
      expect(result.success).toBe(false);
      if (!result.success) {
        const nameError = result.error.issues.find(
          (issue) =>
            issue.path.join(".") ===
              "attrs.arrayNamedObject.value.asArrayNamedObject.0.name" &&
            issue.message === "必須項目です",
        );
        const objectError = result.error.issues.find(
          (issue) =>
            issue.path.join(".") ===
              "attrs.arrayNamedObject.value.asArrayNamedObject.0.object" &&
            issue.message === "必須項目です",
        );
        expect(nameError).toBeDefined();
        expect(objectError).toBeDefined();
      }
    });

    test("number mandatory field error has correct path", () => {
      const value = {
        ...baseValue,
        attrs: {
          number: {
            ...baseValue.attrs.number,
            isMandatory: true,
            value: {
              asNumber: null,
            },
          },
        },
      };

      const result = schema.safeParse(value);
      expect(result.success).toBe(false);
      if (!result.success) {
        const error = result.error.issues.find(
          (issue) =>
            issue.path.join(".") === "attrs.number.value.asNumber" &&
            issue.message === "必須項目です",
        );
        expect(error).toBeDefined();
      }
    });

    test("array number mandatory field error has correct path", () => {
      const value = {
        ...baseValue,
        attrs: {
          arrayNumber: {
            ...baseValue.attrs.arrayNumber,
            isMandatory: true,
            value: {
              asArrayNumber: [],
            },
          },
        },
      };

      const result = schema.safeParse(value);
      expect(result.success).toBe(false);
      if (!result.success) {
        const error = result.error.issues.find(
          (issue) =>
            issue.path.join(".") ===
              "attrs.arrayNumber.value.asArrayNumber.0.value" &&
            issue.message === "必須項目です",
        );
        expect(error).toBeDefined();
      }
    });

    test("group mandatory field error has correct path", () => {
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

      const result = schema.safeParse(value);
      expect(result.success).toBe(false);
      if (!result.success) {
        const error = result.error.issues.find(
          (issue) =>
            issue.path.join(".") === "attrs.group.value.asGroup" &&
            issue.message === "必須項目です",
        );
        expect(error).toBeDefined();
      }
    });

    test("role mandatory field error has correct path", () => {
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

      const result = schema.safeParse(value);
      expect(result.success).toBe(false);
      if (!result.success) {
        const error = result.error.issues.find(
          (issue) =>
            issue.path.join(".") === "attrs.role.value.asRole" &&
            issue.message === "必須項目です",
        );
        expect(error).toBeDefined();
      }
    });
  });
});
