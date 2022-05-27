/**
 * @jest-environment jsdom
 */

import { shallow } from "enzyme";
import React from "react";

import { DjangoContext } from "../../utils/DjangoContext";

import { EditAttributeValue } from "./EditAttributeValue";

const mockHandleChangeAttribute = (e) => undefined;
const mockHandleNarrowDownEntries = (e) => undefined;
const mockHandleNarrowDownGroups = (e) => undefined;
const mockHandleClickDeleteListItem = (e) => undefined;

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
    type: "string",
    elem: "ElemString",
  },
  {
    value: { asString: "fuga" },
    type: "text",
    elem: "ElemString",
  },
  {
    value: { asString: "2022-01-01" },
    type: "date",
    elem: "ElemString",
  },
  {
    value: { asBoolean: true },
    type: "boolean",
    elem: "ElemBool",
  },
  {
    value: { asObject: [{ id: 100, name: "hoge", checked: false }] },
    type: "object",
    elem: "ElemObject",
  },
  {
    value: {
      asNamedObject: { foo: [{ id: 100, name: "hoge", checked: false }] },
    },
    type: "named_object",
    elem: "ElemNamedObject",
  },
  {
    value: { asGroup: [{ id: 100, name: "hoge", checked: false }] },
    type: "group",
    elem: "ElemGroup",
  },
];

const arrayAttributes = [
  {
    value: { asArrayString: ["hoge", "fuga"] },
    type: "array_string",
    elem: "ElemString",
  },
  {
    value: {
      asArrayObject: [
        [{ id: 100, name: "hoge", checked: false }],
        [{ id: 200, name: "fuge", checked: false }],
      ],
    },
    type: "array_object",
    elem: "ElemObject",
  },
  {
    value: {
      asArrayNamedObject: [
        { foo: [{ id: 100, name: "hoge", checked: false }] },
        { bar: [{ id: 200, name: "fuga", checked: false }] },
      ],
    },
    type: "array_named_object",
    elem: "ElemNamedObject",
  },
  {
    value: {
      asArrayGroup: [
        [{ id: 100, name: "hoge", checked: false }],
        [{ id: 200, name: "fuge", checked: false }],
      ],
    },
    type: "array_group",
    elem: "ElemGroup",
  },
];

attributes.forEach((attribute) => {
  it("show EditAttributeValue " + attribute.type, () => {
    const djangoContext = DjangoContext.getInstance();
    const attrName = "hoge";
    const attrValue = attribute.value;
    const attrType = djangoContext.attrTypeValue[attribute.type];
    const wrapper = shallow(
      <EditAttributeValue
        attrName={attrName}
        attrInfo={{
          value: attrValue,
          type: attrType,
        }}
        handleChangeAttribute={mockHandleChangeAttribute}
        handleNarrowDownEntries={mockHandleNarrowDownEntries}
        handleNarrowDownGroups={mockHandleNarrowDownGroups}
        handleClickDeleteListItem={mockHandleClickDeleteListItem}
      />
    );

    expect(wrapper.find(attribute.elem).length).toEqual(1);
    expect(wrapper.find(attribute.elem).prop("attrName")).toEqual(attrName);
    expect(wrapper.find(attribute.elem).prop("attrType")).toEqual(attrType);
    expect(wrapper.find(attribute.elem).prop("attrValue")).toEqual(
      Object.values(attrValue)[0]
    );
  });
});

arrayAttributes.forEach((arrayAttribute) => {
  it("show EditAttributeValue " + arrayAttribute.type, () => {
    const djangoContext = DjangoContext.getInstance();
    const attrName = "hoge";
    const attrValue = arrayAttribute.value;
    const attrType = djangoContext.attrTypeValue[arrayAttribute.type];
    const wrapper = shallow(
      <EditAttributeValue
        attrName={attrName}
        attrInfo={{
          value: attrValue,
          type: attrType,
        }}
        handleChangeAttribute={mockHandleChangeAttribute}
        handleNarrowDownEntries={mockHandleNarrowDownEntries}
        handleNarrowDownGroups={mockHandleNarrowDownGroups}
        handleClickDeleteListItem={mockHandleClickDeleteListItem}
      />
    );

    expect(wrapper.find(arrayAttribute.elem).length).toEqual(2);
    wrapper.find(arrayAttribute.elem).forEach((arrayAttributeElem, i) => {
      expect(arrayAttributeElem.prop("attrName")).toEqual(attrName);
      expect(arrayAttributeElem.prop("attrType")).toEqual(attrType);
      expect(arrayAttributeElem.prop("attrValue")).toEqual(
        Object.values(attrValue)[0][i]
      );
    });
  });
});
