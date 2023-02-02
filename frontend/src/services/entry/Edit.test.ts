/**
 * @jest-environment jsdom
 */

import {
  EditableEntry,
  EditableEntryAttrs,
  EditableEntryAttrValue,
} from "../../components/entry/entryForm/EditableEntry";

import { initializeEntryInfo, isSubmittable } from "./Edit";

import { DjangoContext } from "services/DjangoContext";

Object.defineProperty(window, "django_context", {
  value: {
    user: {
      isSuperuser: true,
    },
  },
  writable: false,
});
const djangoContext = DjangoContext.getInstance();

test("initializeEntryInfo should return expect value", () => {
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
        name: "attr",
        type: djangoContext.attrTypeValue.string,
        isMandatory: true,
        isDeleteInChain: true,
      },
    ],
    webhooks: [],
    isPublic: true,
  };
  expect(initializeEntryInfo(entity)).toStrictEqual({
    name: "",
    attrs: {
      attr: {
        id: 2,
        isMandatory: true,
        schema: {
          id: 2,
          name: "attr",
        },
        type: 2,
        value: {
          asArrayGroup: [],
          asArrayNamedObject: [
            {
              "": null,
            },
          ],
          asArrayObject: [],
          asArrayRole: [],
          asArrayString: [""],
          asBoolean: false,
          asGroup: null,
          asNamedObject: {
            "": null,
          },
          asObject: null,
          asRole: null,
          asString: "",
        },
      },
    },
  });
});

test("isSubmittable() returns false when entryInfo.name is null", () => {
  expect(isSubmittable({ name: null, attrs: {} })).toStrictEqual(false);
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
          schema: {
            id: 1,
            name: "test_schema",
          },
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
          name1: {
            id: 1,
            name: "test_object",
            schema: {
              id: 1,
              name: "test_schema",
            },
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
            schema: {
              id: 1,
              name: "test_schema",
            },
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
    // named_object
    {
      type: djangoContext?.attrTypeValue.array_named_object,
      value: {
        asArrayNamedObject: [
          {
            name1: {
              id: 1,
              name: "test_object",
              schema: {
                id: 1,
                name: "test_schema",
              },
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
        id: 1,
        type: c.type,
        isMandatory: true,
        schema: {
          id: 1,
          name: "test_schema",
        },
        value: c.value,
      },
    };
    const entryInfo: EditableEntry = { name: "test_entry", attrs: attrs };

    expect(isSubmittable(entryInfo)).toStrictEqual(true);
  });
});

test("isSubmittable() returns true when entryInfo is not changed", () => {
  // TBD
});

test("convertAttrsFormatCtoS() returns expected value", () => {
  // TBD
});
