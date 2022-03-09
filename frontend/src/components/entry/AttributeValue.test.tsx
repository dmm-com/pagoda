/**
 * @jest-environment jsdom
 */

import { shallow } from "enzyme";
import React from "react";

import { AttributeValue } from "components/entry/AttributeValue";
import { DjangoContext } from "utils/DjangoContext";

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
    value: "hoge",
    type: "string",
    elem: "ElemString",
  },
  {
    value: "fuga",
    type: "text",
    elem: "ElemString",
  },
  {
    value: "2022-01-01",
    type: "date",
    elem: "ElemString",
  },
  {
    value: true,
    type: "boolean",
    elem: "ElemBool",
  },
  {
    value: "true",
    type: "boolean",
    elem: "ElemBool",
  },
  {
    value: { id: 100, name: "hoge" },
    type: "object",
    elem: "ElemObject",
  },
  {
    value: { foo: { id: 100, name: "hoge" } },
    type: "named_object",
    elem: "ElemNamedObject",
  },
  {
    value: { id: 100, name: "hoge" },
    type: "group",
    elem: "ElemGroup",
  },
];

const arrayAttributes = [
  {
    value: ["hoge", "fuga"],
    type: "array_string",
    elem: "ElemString",
  },
  {
    value: [
      { id: 100, name: "hoge" },
      { id: 200, name: "fuge" },
    ],
    type: "array_object",
    elem: "ElemObject",
  },
  {
    value: [
      { foo: { id: 100, name: "hoge" } },
      { bar: { id: 200, name: "fuga" } },
    ],
    type: "array_named_object",
    elem: "ElemNamedObject",
  },
  {
    value: [
      { id: 100, name: "hoge" },
      { id: 200, name: "fuge" },
    ],
    type: "array_group",
    elem: "ElemGroup",
  },
];

attributes.forEach((attribute) => {
  it("show AttributeValue", () => {
    const djangoContext = DjangoContext.getInstance();
    const wrapper = shallow(
      <AttributeValue
        attrInfo={{
          value: attribute.value,
          type: djangoContext.attrTypeValue[attribute.type],
        }}
      />
    );

    expect(wrapper.find(attribute.elem).length).toEqual(1);
    expect(wrapper.find(attribute.elem).props()).toEqual({
      attrValue: attribute.value,
    });
  });
});

arrayAttributes.forEach((arrayAttributes) => {
  it("show AttributeValue", () => {
    const djangoContext = DjangoContext.getInstance();
    const wrapper = shallow(
      <AttributeValue
        attrInfo={{
          value: arrayAttributes.value,
          type: djangoContext.attrTypeValue[arrayAttributes.type],
        }}
      />
    );

    expect(wrapper.find(arrayAttributes.elem).length).toEqual(2);
    wrapper.find(arrayAttributes.elem).forEach((arrayAttributesElem, i) => {
      expect(arrayAttributesElem.props()).toEqual({
        attrValue: arrayAttributes.value[i],
      });
    });
  });
});
