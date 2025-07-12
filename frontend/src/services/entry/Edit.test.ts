/**
 * @jest-environment jsdom
 */

import {
  EntryAttributeValueType,
  convertAttrsFormatCtoS,
  formalizeEntryInfo,
} from "./Edit";

import { EntryAttributeTypeTypeEnum } from "@dmm-com/airone-apiclient-typescript-fetch";
import {
  EditableEntryAttrValue,
  EditableEntryAttrs,
} from "components/entry/entryForm/EditableEntry";

Object.defineProperty(window, "django_context", {
  value: {
    user: {
      isSuperuser: true,
    },
  },
  writable: false,
});

test("formalizeEntryInfo should return expect value", () => {
  const entity = {
    id: 1,
    name: "TestEntity",
    note: "hoge",
    status: 0,
    isToplevel: true,
    hasOngoingChanges: false,
    attrs: [
      {
        id: 2,
        index: 0,
        name: "string",
        type: EntryAttributeTypeTypeEnum.STRING,
        isMandatory: true,
        isDeleteInChain: true,
        isWritable: true,
        isSummarized: false,
        referral: [],
        note: "",
      },
      {
        id: 3,
        index: 1,
        name: "array_string",
        type: EntryAttributeTypeTypeEnum.ARRAY_STRING,
        isMandatory: false,
        isDeleteInChain: true,
        isWritable: true,
        isSummarized: false,
        referral: [],
        note: "",
      },
      {
        id: 4,
        index: 2,
        name: "array_named_object",
        type: EntryAttributeTypeTypeEnum.ARRAY_NAMED_OBJECT,
        isMandatory: true,
        isDeleteInChain: true,
        isWritable: true,
        isSummarized: false,
        referral: [],
        note: "",
      },
    ],
    webhooks: [],
    isPublic: true,
  };

  expect(formalizeEntryInfo(undefined, entity, [])).toStrictEqual({
    name: "",
    schema: {
      id: 1,
      name: "TestEntity",
    },
    attrs: {
      2: {
        index: 0,
        isMandatory: true,
        schema: {
          id: 2,
          name: "string",
        },
        type: 2,
        value: {
          asString: "",
          asBoolean: false,
          asArrayString: [{ value: "" }],
          asArrayObject: [],
          asArrayGroup: [],
          asArrayRole: [],
          asArrayNamedObject: [{ name: "", object: null, _boolean: false }],
          asNumber: null,
          asArrayNumber: [{ value: null }],
          asObject: null,
          asGroup: null,
          asRole: null,
          asNamedObject: { name: "", object: null },
        },
      },
      3: {
        index: 1,
        isMandatory: false,
        schema: {
          id: 3,
          name: "array_string",
        },
        type: 1026,
        value: {
          asString: "",
          asBoolean: false,
          asArrayString: [{ value: "" }],
          asArrayObject: [],
          asArrayGroup: [],
          asArrayRole: [],
          asArrayNamedObject: [{ name: "", object: null, _boolean: false }],
          asNumber: null,
          asArrayNumber: [{ value: null }],
          asObject: null,
          asGroup: null,
          asRole: null,
          asNamedObject: { name: "", object: null },
        },
      },
      4: {
        index: 2,
        isMandatory: true,
        schema: {
          id: 4,
          name: "array_named_object",
        },
        type: 3073,
        value: {
          asString: "",
          asBoolean: false,
          asArrayString: [{ value: "" }],
          asArrayObject: [],
          asArrayGroup: [],
          asArrayRole: [],
          asArrayNamedObject: [{ name: "", object: null, _boolean: false }],
          asNumber: null,
          asArrayNumber: [{ value: null }],
          asObject: null,
          asGroup: null,
          asRole: null,
          asNamedObject: { name: "", object: null },
        },
      },
    },
  });

  const entry = {
    id: 10,
    name: "TestEntry",
    schema: {
      id: 1,
      name: "TestEnttity",
    },
    isActive: true,
    deletedUser: null,
    attrs: [
      {
        id: 20,
        index: 0,
        name: "string",
        schema: {
          id: 2,
          name: "string",
        },
        type: EntryAttributeTypeTypeEnum.STRING,
        isMandatory: true,
        isReadable: true,
        value: {
          asString: "",
        },
      },
      {
        id: 30,
        index: 1,
        name: "array_string",
        schema: {
          id: 3,
          name: "array_string",
        },
        type: EntryAttributeTypeTypeEnum.ARRAY_STRING,
        isMandatory: false,
        isReadable: true,
        value: {
          asArrayString: [],
        },
      },
      {
        id: 40,
        index: 2,
        name: "array_named_object",
        schema: {
          id: 4,
          name: "array_named_object",
        },
        type: EntryAttributeTypeTypeEnum.ARRAY_NAMED_OBJECT,
        isMandatory: true,
        isReadable: true,
        value: {
          asArrayNamedObject: [],
        },
      },
    ],
  };

  expect(formalizeEntryInfo(entry, entity, [])).toStrictEqual({
    name: "TestEntry",
    schema: {
      id: 1,
      name: "TestEntity",
    },
    attrs: {
      2: {
        index: 0,
        isMandatory: true,
        schema: {
          id: 2,
          name: "string",
        },
        type: 2,
        value: {
          asString: "",
        },
      },
      3: {
        index: 1,
        isMandatory: false,
        schema: {
          id: 3,
          name: "array_string",
        },
        type: 1026,
        value: {
          asArrayString: [{ value: "" }],
        },
      },
      4: {
        index: 2,
        isMandatory: true,
        schema: {
          id: 4,
          name: "array_named_object",
        },
        type: 3073,
        value: {
          asArrayNamedObject: [{ name: "", object: null, _boolean: false }],
        },
      },
    },
  });
});

test("formalizeEntryInfo should use defaultValue when creating new entry", () => {
  const entity = {
    id: 1,
    name: "TestEntity",
    note: "hoge",
    status: 0,
    isToplevel: true,
    hasOngoingChanges: false,
    attrs: [
      {
        id: 2,
        index: 0,
        name: "string_with_default",
        type: EntryAttributeTypeTypeEnum.STRING,
        isMandatory: true,
        isDeleteInChain: true,
        isWritable: true,
        isSummarized: false,
        referral: [],
        note: "",
        defaultValue: { asString: "default string value" },
      },
      {
        id: 3,
        index: 1,
        name: "boolean_with_default",
        type: EntryAttributeTypeTypeEnum.BOOLEAN,
        isMandatory: false,
        isDeleteInChain: true,
        isWritable: true,
        isSummarized: false,
        referral: [],
        note: "",
        defaultValue: { asBoolean: true },
      },
      {
        id: 4,
        index: 2,
        name: "text_with_default",
        type: EntryAttributeTypeTypeEnum.TEXT,
        isMandatory: false,
        isDeleteInChain: true,
        isWritable: true,
        isSummarized: false,
        referral: [],
        note: "",
        defaultValue: { asString: "default\ntext\nvalue" },
      },
      {
        id: 5,
        index: 3,
        name: "string_without_default",
        type: EntryAttributeTypeTypeEnum.STRING,
        isMandatory: false,
        isDeleteInChain: true,
        isWritable: true,
        isSummarized: false,
        referral: [],
        note: "",
        defaultValue: null,
      },
    ],
    webhooks: [],
    isPublic: true,
  };

  const result = formalizeEntryInfo(undefined, entity, []);

  // Check string attribute with default value
  expect(result.attrs[2].value.asString).toBe("default string value");

  // Check boolean attribute with default value
  expect(result.attrs[3].value.asBoolean).toBe(true);

  // Check text attribute with default value
  expect(result.attrs[4].value.asString).toBe("default\ntext\nvalue");

  // Check string attribute without default value (should use empty string)
  expect(result.attrs[5].value.asString).toBe("");
});

test("convertAttrsFormatCtoS() returns expected value", () => {
  const cases: Array<{
    client_data: {
      type: (typeof EntryAttributeTypeTypeEnum)[keyof typeof EntryAttributeTypeTypeEnum];
      value: EditableEntryAttrValue;
    };
    expected_data: EntryAttributeValueType;
  }> = [
    // boolean
    {
      client_data: {
        type: EntryAttributeTypeTypeEnum.BOOLEAN,
        value: {
          asBoolean: true,
        },
      },
      expected_data: true,
    },
    // string
    {
      client_data: {
        type: EntryAttributeTypeTypeEnum.STRING,
        value: {
          asString: "value",
        },
      },
      expected_data: "value",
    },
    // number
    {
      client_data: {
        type: EntryAttributeTypeTypeEnum.NUMBER,
        value: {
          asNumber: 2,
        },
      },
      expected_data: 2,
    },
    // object
    {
      client_data: {
        type: EntryAttributeTypeTypeEnum.OBJECT,
        value: {
          asObject: {
            id: 3,
            name: "test_object",
          },
        },
      },
      expected_data: 3,
    },
    // group
    {
      client_data: {
        type: EntryAttributeTypeTypeEnum.GROUP,
        value: {
          asGroup: {
            id: 2,
            name: "test_object",
          },
        },
      },
      expected_data: 2,
    },
    // named_object
    {
      client_data: {
        type: EntryAttributeTypeTypeEnum.NAMED_OBJECT,
        value: {
          asNamedObject: {
            name: "hoge",
            object: {
              id: 2,
              name: "test_object",
            },
          },
        },
      },
      expected_data: {
        id: 2,
        name: "hoge",
      },
    },
    // array_string
    {
      client_data: {
        type: EntryAttributeTypeTypeEnum.ARRAY_STRING,
        value: {
          asArrayString: [{ value: "value" }],
        },
      },
      expected_data: ["value"],
    },
    // array_object
    {
      client_data: {
        type: EntryAttributeTypeTypeEnum.ARRAY_OBJECT,
        value: {
          asArrayObject: [
            {
              id: 2,
              name: "test_object",
            },
          ],
        },
      },
      expected_data: [2],
    },
    // array_group
    {
      client_data: {
        type: EntryAttributeTypeTypeEnum.ARRAY_GROUP,
        value: {
          asArrayGroup: [
            {
              id: 2,
              name: "test_object",
            },
          ],
        },
      },
      expected_data: [2],
    },
    // array_named_object
    {
      client_data: {
        type: EntryAttributeTypeTypeEnum.ARRAY_NAMED_OBJECT,
        value: {
          asArrayNamedObject: [
            {
              name: "name1",
              object: {
                id: 2,
                name: "test_object",
              },
              _boolean: false,
            },
          ],
        },
      },
      expected_data: [
        {
          id: 2,
          name: "name1",
        },
      ],
    },
    // role
    {
      client_data: {
        type: EntryAttributeTypeTypeEnum.ROLE,
        value: {
          asRole: {
            id: 2,
            name: "test_role",
          },
        },
      },
      expected_data: 2,
    },
    // array_role
    {
      client_data: {
        type: EntryAttributeTypeTypeEnum.ARRAY_ROLE,
        value: {
          asArrayRole: [
            {
              id: 2,
              name: "test_role",
            },
          ],
        },
      },
      expected_data: [2],
    },
    // array_number
    {
      client_data: {
        type: EntryAttributeTypeTypeEnum.ARRAY_NUMBER,
        value: {
          asArrayNumber: [{ value: 123 }, { value: 456 }],
        },
      },
      expected_data: [123, 456],
    },
  ];

  cases.forEach((c) => {
    const attrs: Record<string, EditableEntryAttrs> = {
      key: {
        index: 0,
        type: c.client_data.type,
        isMandatory: true,
        schema: {
          id: 1,
          name: "test",
        },
        value: c.client_data.value,
      },
    };
    const sending_data = convertAttrsFormatCtoS(attrs);

    expect(sending_data).toStrictEqual([
      {
        id: 1,
        value: c.expected_data,
      },
    ]);
  });
});

test("formalizeEntryInfo should use defaultValue when creating new entry", () => {
  const entity = {
    id: 1,
    name: "TestEntity",
    note: "hoge",
    status: 0,
    isToplevel: true,
    hasOngoingChanges: false,
    attrs: [
      {
        id: 2,
        index: 0,
        name: "string_with_default",
        type: EntryAttributeTypeTypeEnum.STRING,
        isMandatory: true,
        isDeleteInChain: true,
        isWritable: true,
        isSummarized: false,
        referral: [],
        note: "",
        defaultValue: { asString: "default string value" },
      },
      {
        id: 3,
        index: 1,
        name: "boolean_with_default",
        type: EntryAttributeTypeTypeEnum.BOOLEAN,
        isMandatory: false,
        isDeleteInChain: true,
        isWritable: true,
        isSummarized: false,
        referral: [],
        note: "",
        defaultValue: { asBoolean: true },
      },
      {
        id: 4,
        index: 2,
        name: "text_with_default",
        type: EntryAttributeTypeTypeEnum.TEXT,
        isMandatory: false,
        isDeleteInChain: true,
        isWritable: true,
        isSummarized: false,
        referral: [],
        note: "",
        defaultValue: { asString: "default\ntext\nvalue" },
      },
      {
        id: 5,
        index: 3,
        name: "string_without_default",
        type: EntryAttributeTypeTypeEnum.STRING,
        isMandatory: false,
        isDeleteInChain: true,
        isWritable: true,
        isSummarized: false,
        referral: [],
        note: "",
        defaultValue: null,
      },
    ],
    webhooks: [],
    isPublic: true,
  };

  const result = formalizeEntryInfo(undefined, entity, []);

  // Check string attribute with default value
  expect(result.attrs[2].value.asString).toBe("default string value");

  // Check boolean attribute with default value
  expect(result.attrs[3].value.asBoolean).toBe(true);

  // Check text attribute with default value
  expect(result.attrs[4].value.asString).toBe("default\ntext\nvalue");

  // Check string attribute without default value (should use empty string)
  expect(result.attrs[5].value.asString).toBe("");
});

test("convertAttrsFormatCtoS() should return expected value", () => {
  const client_data: Record<string, EditableEntryAttrs> = {
    key: {
      index: 0,
      type: EntryAttributeTypeTypeEnum.BOOLEAN,
      isMandatory: true,
      schema: {
        id: 1,
        name: "test",
      },
      value: {
        asBoolean: true,
      },
    },
  };

  const sending_data = convertAttrsFormatCtoS(client_data);

  expect(sending_data).toStrictEqual([
    {
      id: 1,
      value: true,
    },
  ]);
});

test("convertAttrsFormatCtoS() returns expected value when nothing value", () => {
  const cases: Array<{
    client_data: {
      type: (typeof EntryAttributeTypeTypeEnum)[keyof typeof EntryAttributeTypeTypeEnum];
      value: EditableEntryAttrValue;
    };
    expected_data: EntryAttributeValueType;
  }> = [
    // boolean
    {
      client_data: {
        type: EntryAttributeTypeTypeEnum.BOOLEAN,
        value: {
          asBoolean: false,
        },
      },
      expected_data: false,
    },
    // string
    {
      client_data: {
        type: EntryAttributeTypeTypeEnum.STRING,
        value: {
          asString: "",
        },
      },
      expected_data: "",
    },
    // number
    {
      client_data: {
        type: EntryAttributeTypeTypeEnum.NUMBER,
        value: {
          asNumber: null,
        },
      },
      expected_data: null,
    },
    // object
    {
      client_data: {
        type: EntryAttributeTypeTypeEnum.OBJECT,
        value: {
          asObject: undefined,
        },
      },
      expected_data: null,
    },
    // group
    {
      client_data: {
        type: EntryAttributeTypeTypeEnum.GROUP,
        value: {
          asGroup: undefined,
        },
      },
      expected_data: null,
    },
    // named_object
    {
      client_data: {
        type: EntryAttributeTypeTypeEnum.NAMED_OBJECT,
        value: {
          asNamedObject: { name: "", object: null },
        },
      },
      expected_data: {
        id: null,
        name: "",
      },
    },
    // array_string
    {
      client_data: {
        type: EntryAttributeTypeTypeEnum.ARRAY_STRING,
        value: {
          asArrayString: [],
        },
      },
      expected_data: [],
    },
    // array_object
    {
      client_data: {
        type: EntryAttributeTypeTypeEnum.ARRAY_OBJECT,
        value: {
          asArrayObject: [],
        },
      },
      expected_data: [],
    },
    // array_group
    {
      client_data: {
        type: EntryAttributeTypeTypeEnum.ARRAY_GROUP,
        value: {
          asArrayGroup: [],
        },
      },
      expected_data: [],
    },
    // array_named_object
    {
      client_data: {
        type: EntryAttributeTypeTypeEnum.ARRAY_NAMED_OBJECT,
        value: {
          asArrayNamedObject: [],
        },
      },
      expected_data: [],
    },
    // role
    {
      client_data: {
        type: EntryAttributeTypeTypeEnum.ROLE,
        value: {
          asRole: undefined,
        },
      },
      expected_data: null,
    },
    // array_role
    {
      client_data: {
        type: EntryAttributeTypeTypeEnum.ARRAY_ROLE,
        value: {
          asArrayRole: [],
        },
      },
      expected_data: [],
    },
    // array_number
    {
      client_data: {
        type: EntryAttributeTypeTypeEnum.ARRAY_NUMBER,
        value: {
          asArrayNumber: [],
        },
      },
      expected_data: [],
    },
  ];

  cases.forEach((c) => {
    const attrs: Record<string, EditableEntryAttrs> = {
      key: {
        index: 0,
        type: c.client_data.type,
        isMandatory: true,
        schema: {
          id: 1,
          name: "test",
        },
        value: c.client_data.value,
      },
    };
    const sending_data = convertAttrsFormatCtoS(attrs);

    expect(sending_data).toStrictEqual([
      {
        id: 1,
        value: c.expected_data,
      },
    ]);
  });
});

test("formalizeEntryInfo should use defaultValue when creating new entry", () => {
  const entity = {
    id: 1,
    name: "TestEntity",
    note: "hoge",
    status: 0,
    isToplevel: true,
    hasOngoingChanges: false,
    attrs: [
      {
        id: 2,
        index: 0,
        name: "string_with_default",
        type: EntryAttributeTypeTypeEnum.STRING,
        isMandatory: true,
        isDeleteInChain: true,
        isWritable: true,
        isSummarized: false,
        referral: [],
        note: "",
        defaultValue: { asString: "default string value" },
      },
      {
        id: 3,
        index: 1,
        name: "boolean_with_default",
        type: EntryAttributeTypeTypeEnum.BOOLEAN,
        isMandatory: false,
        isDeleteInChain: true,
        isWritable: true,
        isSummarized: false,
        referral: [],
        note: "",
        defaultValue: { asBoolean: true },
      },
      {
        id: 4,
        index: 2,
        name: "text_with_default",
        type: EntryAttributeTypeTypeEnum.TEXT,
        isMandatory: false,
        isDeleteInChain: true,
        isWritable: true,
        isSummarized: false,
        referral: [],
        note: "",
        defaultValue: { asString: "default\ntext\nvalue" },
      },
      {
        id: 5,
        index: 3,
        name: "string_without_default",
        type: EntryAttributeTypeTypeEnum.STRING,
        isMandatory: false,
        isDeleteInChain: true,
        isWritable: true,
        isSummarized: false,
        referral: [],
        note: "",
        defaultValue: null,
      },
    ],
    webhooks: [],
    isPublic: true,
  };

  const result = formalizeEntryInfo(undefined, entity, []);

  // Check string attribute with default value
  expect(result.attrs[2].value.asString).toBe("default string value");

  // Check boolean attribute with default value
  expect(result.attrs[3].value.asBoolean).toBe(true);

  // Check text attribute with default value
  expect(result.attrs[4].value.asString).toBe("default\ntext\nvalue");

  // Check string attribute without default value (should use empty string)
  expect(result.attrs[5].value.asString).toBe("");
});
