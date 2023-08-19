/**
 * @jest-environment jsdom
 */

import { shallow } from "enzyme";
import React from "react";

import {
  EntryAttributeTypeTypeEnum,
  EntryAttributeValue,
} from "@dmm-com/airone-apiclient-typescript-fetch";
import { AttributeValue } from "components/entry/AttributeValue";

beforeAll(() => {
  Object.defineProperty(window, "django_context", {
    value: {
      version: "v0.0.1-test",
      user: {
        id: 123,
        isSuperuser: true,
      },
    },
    writable: false,
  });
});

const attributes = [
  {
    value: { asString: "hoge" },
    type: EntryAttributeTypeTypeEnum.STRING,
    elem: "ElemString",
  },
  {
    value: { asString: "fuga" },
    type: EntryAttributeTypeTypeEnum.TEXT,
    elem: "ElemString",
  },
  {
    value: { asString: "2022-01-01" },
    type: EntryAttributeTypeTypeEnum.DATE,
    elem: "ElemString",
  },
  {
    value: { asBoolean: true },
    type: EntryAttributeTypeTypeEnum.BOOLEAN,
    elem: "ElemBool",
  },
  {
    value: { asObject: { id: 100, name: "hoge" } },
    type: EntryAttributeTypeTypeEnum.OBJECT,
    elem: "ElemObject",
  },
  {
    value: { asNamedObject: { foo: { id: 100, name: "hoge" } } },
    type: EntryAttributeTypeTypeEnum.NAMED_OBJECT,
    elem: "ElemNamedObject",
  },
  {
    value: { asGroup: { id: 100, name: "hoge" } },
    type: EntryAttributeTypeTypeEnum.GROUP,
    elem: "ElemGroup",
  },
];

const arrayAttributes = [
  {
    value: { asArrayString: ["hoge", "fuga"] },
    type: EntryAttributeTypeTypeEnum.ARRAY_STRING,
    elem: "ElemString",
  },
  {
    value: {
      asArrayObject: [
        { id: 100, name: "hoge" },
        { id: 200, name: "fuge" },
      ],
    },
    type: EntryAttributeTypeTypeEnum.ARRAY_OBJECT,
    elem: "ElemObject",
  },
  {
    value: {
      asArrayNamedObject: [
        { foo: { id: 100, name: "hoge" } },
        { bar: { id: 200, name: "fuga" } },
      ],
    },
    type: EntryAttributeTypeTypeEnum.ARRAY_NAMED_OBJECT,
    elem: "ElemNamedObject",
  },
  {
    value: {
      asArrayGroup: [
        { id: 100, name: "hoge" },
        { id: 200, name: "fuge" },
      ],
    },
    type: EntryAttributeTypeTypeEnum.ARRAY_GROUP,
    elem: "ElemGroup",
  },
];

attributes.forEach((attribute) => {
  it("show AttributeValue", () => {
    const wrapper = shallow(
      <AttributeValue
        attrInfo={{
          value: attribute.value as EntryAttributeValue,
          type: attribute.type,
        }}
      />
    );

    expect(wrapper.find(attribute.elem).length).toEqual(1);
    expect(wrapper.find(attribute.elem).props()).toEqual({
      attrValue: Object.values(attribute.value)[0],
    });
  });
});

arrayAttributes.forEach((arrayAttributes) => {
  it("show AttributeValue", () => {
    const wrapper = shallow(
      <AttributeValue
        attrInfo={{
          value: arrayAttributes.value as EntryAttributeValue,
          type: arrayAttributes.type,
        }}
      />
    );

    expect(wrapper.find(arrayAttributes.elem).length).toEqual(2);
    wrapper.find(arrayAttributes.elem).forEach((arrayAttributesElem, i) => {
      expect(arrayAttributesElem.props()).toEqual({
        attrValue: Object.values(arrayAttributes.value)[0][i],
      });
    });
  });
});
