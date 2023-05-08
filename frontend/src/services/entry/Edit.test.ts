/**
 * @jest-environment jsdom
 */

Object.defineProperty(window, "django_context", {
  value: {
    user: {
      isSuperuser: true,
    },
  },
  writable: false,
});

import {
  formalizeEntryInfo,
  isSubmittable,
  convertAttrsFormatCtoS,
} from "./Edit";

import {
  EditableEntry,
  EditableEntryAttrs,
  EditableEntryAttrValue,
} from "components/entry/entryForm/EditableEntry";
import { DjangoContext } from "services/DjangoContext";

const djangoContext = DjangoContext.getInstance();

test("formalizeEntryInfo should return expect value", () => {
  const entity = {
    id: 1,
    name: "TestEntity",
    note: "hoge",
    status: 0,
    isToplevel: true,
    attrs: [
      {
        id: 2,
        index: 0,
        name: "string",
        type: djangoContext?.attrTypeValue.string,
        isMandatory: true,
        isDeleteInChain: true,
        referral: [],
      },
      {
        id: 3,
        index: 1,
        name: "array_string",
        type: djangoContext?.attrTypeValue.array_string,
        isMandatory: false,
        isDeleteInChain: true,
        referral: [],
      },
      {
        id: 4,
        index: 2,
        name: "array_named_object",
        type: djangoContext?.attrTypeValue.array_named_object,
        isMandatory: true,
        isDeleteInChain: true,
        referral: [],
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
          asArrayGroup: [],
          asArrayNamedObject: [{}],
          asArrayObject: [],
          asArrayRole: [],
          asArrayString: [""],
          asBoolean: false,
          asGroup: undefined,
          asNamedObject: {},
          asObject: undefined,
          asRole: undefined,
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
          asArrayGroup: [],
          asArrayNamedObject: [{}],
          asArrayObject: [],
          asArrayRole: [],
          asArrayString: [""],
          asBoolean: false,
          asGroup: undefined,
          asNamedObject: {},
          asObject: undefined,
          asRole: undefined,
          asString: "",
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
          asArrayGroup: [],
          asArrayNamedObject: [{}],
          asArrayObject: [],
          asArrayRole: [],
          asArrayString: [""],
          asBoolean: false,
          asGroup: undefined,
          asNamedObject: {},
          asObject: undefined,
          asRole: undefined,
          asString: "",
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
        type: djangoContext?.attrTypeValue.string,
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
        type: djangoContext?.attrTypeValue.array_string,
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
        type: djangoContext?.attrTypeValue.array_named_object,
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
          asArrayString: [""],
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
          asArrayNamedObject: [{}],
        },
      },
    },
  });
});

test("isSubmittable() returns true when entryInfo.attrs is changed", () => {
  const cases: Array<{ type: number; value: EditableEntryAttrValue }> = [
    // boolean
    {
      type: djangoContext?.attrTypeValue.boolean,
      value: {
        asBoolean: true,
      },
    },
    // string
    {
      type: djangoContext?.attrTypeValue.string,
      value: {
        asString: "value",
      },
    },
    // object
    {
      type: djangoContext?.attrTypeValue.object,
      value: {
        asObject: {
          id: 1,
          name: "test_object",
          _boolean: false,
        },
      },
    },
    // group
    {
      type: djangoContext?.attrTypeValue.group,
      value: {
        asGroup: {
          id: 1,
          name: "test_object",
        },
      },
    },
    // named_object
    {
      type: djangoContext?.attrTypeValue.named_object,
      value: {
        asNamedObject: {
          hoge: {
            id: 1,
            name: "test_object",
            _boolean: false,
          },
        },
      },
    },
    // array_string
    {
      type: djangoContext?.attrTypeValue.array_string,
      value: {
        asArrayString: ["value"],
      },
    },
    // array_object
    {
      type: djangoContext?.attrTypeValue.array_object,
      value: {
        asArrayObject: [
          {
            id: 1,
            name: "test_object",
            _boolean: false,
          },
        ],
      },
    },
    // array_group
    {
      type: djangoContext?.attrTypeValue.array_group,
      value: {
        asArrayGroup: [
          {
            id: 1,
            name: "test_object",
          },
        ],
      },
    },
    // array_named_object
    {
      type: djangoContext?.attrTypeValue.array_named_object,
      value: {
        asArrayNamedObject: [
          {
            name1: {
              id: 1,
              name: "test_object",
              _boolean: false,
            },
          },
        ],
      },
    },

    // TODO role
    // TODO array_role
  ];

  cases.forEach((c) => {
    const attrs: Record<string, EditableEntryAttrs> = {
      key: {
        index: 0,
        type: c.type,
        isMandatory: true,
        schema: {
          id: 1,
          name: "test",
        },
        value: c.value,
      },
    };
    const entryInfo: EditableEntry = {
      name: "test_entry",
      schema: { id: 0, name: "testEntity" },
      attrs: attrs,
    };

    expect(isSubmittable(entryInfo)).toStrictEqual(true);
  });
});

test("isSubmittable() returns false when entryInfo is wrong value", () => {
  const cases: Array<{ type: number; value: EditableEntryAttrValue }> = [
    // string
    {
      type: djangoContext?.attrTypeValue.string,
      value: {
        asString: "",
      },
    },
    // object
    {
      type: djangoContext?.attrTypeValue.object,
      value: {},
    },
    // group
    {
      type: djangoContext?.attrTypeValue.group,
      value: {},
    },
    // named_object
    {
      type: djangoContext?.attrTypeValue.named_object,
      value: {
        asNamedObject: {
          "": {
            id: 1,
            name: "test_object",
            _boolean: false,
          },
        },
      },
    },
    // TODO case object is none
    /*
    {
      type: djangoContext?.attrTypeValue.named_object,
      value: {
        asNamedObject: {
          name1: {}
        },
      },
    },
    */
    // array_string
    {
      type: djangoContext?.attrTypeValue.array_string,
      value: {
        asArrayString: [],
      },
    },
    // array_object
    {
      type: djangoContext?.attrTypeValue.array_object,
      value: {
        asArrayObject: [],
      },
    },
    // array_group
    {
      type: djangoContext?.attrTypeValue.array_group,
      value: {
        asArrayGroup: [],
      },
    },
    // named_object
    {
      type: djangoContext?.attrTypeValue.array_named_object,
      value: {
        asArrayNamedObject: [],
      },
    },
    {
      type: djangoContext?.attrTypeValue.array_named_object,
      value: {
        asArrayNamedObject: [
          {
            "": {
              id: 1,
              name: "test_object",
              _boolean: false,
            },
          },
        ],
      },
    },
    // TODO case object is none
    /*
    {
      type: djangoContext?.attrTypeValue.array_named_object,
      value: {
        asArrayNamedObject: [
          {
            name1: {}
          },
        ],
      },
    },
    */

    // TODO role
    // TODO array_role
  ];

  cases.forEach((c) => {
    const attrs: Record<string, EditableEntryAttrs> = {
      key: {
        index: 0,
        type: c.type,
        isMandatory: true,
        schema: {
          id: 1,
          name: "test",
        },
        value: c.value,
      },
    };
    const entryInfo: EditableEntry = {
      name: "test_entry",
      schema: { id: 0, name: "testEntity" },
      attrs: attrs,
    };
    expect(isSubmittable(entryInfo)).toStrictEqual(false);
  });
});
test("convertAttrsFormatCtoS() returns expected value", () => {
  const cases: Array<{
    client_data: { type: number; value: EditableEntryAttrValue };
    expected_data: any;
  }> = [
    // boolean
    {
      client_data: {
        type: djangoContext?.attrTypeValue.boolean,
        value: {
          asBoolean: true,
        },
      },
      expected_data: true,
    },
    // string
    {
      client_data: {
        type: djangoContext?.attrTypeValue.string,
        value: {
          asString: "value",
        },
      },
      expected_data: "value",
    },
    // object
    {
      client_data: {
        type: djangoContext?.attrTypeValue.object,
        value: {
          asObject: {
            id: 3,
            name: "test_object",
            _boolean: false,
          },
        },
      },
      expected_data: 3,
    },
    // group
    {
      client_data: {
        type: djangoContext?.attrTypeValue.group,
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
        type: djangoContext?.attrTypeValue.named_object,
        value: {
          asNamedObject: {
            hoge: {
              id: 2,
              name: "test_object",
              _boolean: false,
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
        type: djangoContext?.attrTypeValue.array_string,
        value: {
          asArrayString: ["value"],
        },
      },
      expected_data: ["value"],
    },
    // array_object
    {
      client_data: {
        type: djangoContext?.attrTypeValue.array_object,
        value: {
          asArrayObject: [
            {
              id: 2,
              name: "test_object",
              _boolean: false,
            },
          ],
        },
      },
      expected_data: [2],
    },
    // array_group
    {
      client_data: {
        type: djangoContext?.attrTypeValue.array_group,
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
        type: djangoContext?.attrTypeValue.array_named_object,
        value: {
          asArrayNamedObject: [
            {
              name1: {
                id: 2,
                name: "test_object",
                _boolean: false,
              },
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
        type: djangoContext?.attrTypeValue.role,
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
        type: djangoContext?.attrTypeValue.array_role,
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

test("convertAttrsFormatCtoS() returns expected value when nothing value", () => {
  const cases: Array<{
    client_data: { type: number; value: EditableEntryAttrValue };
    expected_data: any;
  }> = [
    // boolean
    {
      client_data: {
        type: djangoContext?.attrTypeValue.boolean,
        value: {
          asBoolean: false,
        },
      },
      expected_data: false,
    },
    // string
    {
      client_data: {
        type: djangoContext?.attrTypeValue.string,
        value: {
          asString: "",
        },
      },
      expected_data: "",
    },
    // object
    {
      client_data: {
        type: djangoContext?.attrTypeValue.object,
        value: {
          asObject: undefined,
        },
      },
      expected_data: null,
    },
    // group
    {
      client_data: {
        type: djangoContext?.attrTypeValue.group,
        value: {
          asGroup: undefined,
        },
      },
      expected_data: null,
    },
    // named_object
    {
      client_data: {
        type: djangoContext?.attrTypeValue.named_object,
        value: {
          asNamedObject: {},
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
        type: djangoContext?.attrTypeValue.array_string,
        value: {
          asArrayString: [],
        },
      },
      expected_data: [],
    },
    // array_object
    {
      client_data: {
        type: djangoContext?.attrTypeValue.array_object,
        value: {
          asArrayObject: [],
        },
      },
      expected_data: [],
    },
    // array_group
    {
      client_data: {
        type: djangoContext?.attrTypeValue.array_group,
        value: {
          asArrayGroup: [],
        },
      },
      expected_data: [],
    },
    // array_named_object
    {
      client_data: {
        type: djangoContext?.attrTypeValue.array_named_object,
        value: {
          asArrayNamedObject: [],
        },
      },
      expected_data: [],
    },
    // role
    {
      client_data: {
        type: djangoContext?.attrTypeValue.role,
        value: {
          asRole: undefined,
        },
      },
      expected_data: null,
    },
    // array_role
    {
      client_data: {
        type: djangoContext?.attrTypeValue.array_role,
        value: {
          asArrayRole: [],
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
