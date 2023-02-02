/**
 * @jest-environment jsdom
 */

import { shallow } from "enzyme";
import React from "react";

import { DjangoContext } from "../../../services/DjangoContext";

import { EditAttributeValue } from "./EditAttributeValue";
import { EditableEntryAttrValue } from "./EditableEntry";

const mockHandleChangeAttribute = () => undefined;
const mockHandleClickDeleteListItem = () => undefined;
const mockHandleClickAddListItem = () => undefined;

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
    elem: "ElemDate",
  },
  {
    value: { asBoolean: true },
    type: "boolean",
    elem: "ElemBool",
  },
  {
    value: { asObject: { id: 100, name: "hoge", checked: false } },
    type: "object",
    elem: "ElemReferral",
  },
  {
    value: {
      asNamedObject: { foo: { id: 100, name: "hoge", checked: false } },
    },
    type: "named_object",
    elem: "ElemNamedObject",
  },
  {
    value: { asGroup: { id: 100, name: "hoge", checked: false } },
    type: "group",
    elem: "ElemReferral",
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
        { id: 100, name: "hoge", checked: false },
        { id: 200, name: "fuge", checked: false },
      ],
    },
    type: "array_object",
    elem: "ElemReferral",
  },
  {
    value: {
      asArrayNamedObject: [
        { foo: { id: 100, name: "hoge", checked: false } },
        { bar: { id: 200, name: "fuga", checked: false } },
      ],
    },
    type: "array_named_object",
    elem: "ElemNamedObject",
  },
  {
    value: {
      asArrayGroup: [
        { id: 100, name: "hoge", checked: false },
        { id: 200, name: "fuge", checked: false },
      ],
    },
    type: "array_group",
    elem: "ElemReferral",
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
          id: 9999,
          value: attrValue as EditableEntryAttrValue,
          type: attrType,
          isMandatory: false,
          schema: {
            id: 9999,
            name: "hoge",
          },
        }}
        handleChangeAttribute={mockHandleChangeAttribute}
        handleClickDeleteListItem={mockHandleClickDeleteListItem}
        handleClickAddListItem={mockHandleClickAddListItem}
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
          id: 9999,
          value: attrValue as EditableEntryAttrValue,
          type: attrType,
          isMandatory: false,
          schema: {
            id: 9999,
            name: "hoge",
          },
        }}
        handleChangeAttribute={mockHandleChangeAttribute}
        handleClickDeleteListItem={mockHandleClickDeleteListItem}
        handleClickAddListItem={mockHandleClickAddListItem}
      />
    );

    if (
      arrayAttribute.type == "array_group" ||
      arrayAttribute.type == "array_object"
    ) {
      expect(wrapper.find(arrayAttribute.elem).length).toEqual(1);
      wrapper.find(arrayAttribute.elem).forEach((arrayAttributeElem) => {
        expect(arrayAttributeElem.prop("attrName")).toEqual(attrName);
        expect(arrayAttributeElem.prop("attrType")).toEqual(attrType);
      });
    } else {
      expect(wrapper.find(arrayAttribute.elem).length).toEqual(2);
      wrapper.find(arrayAttribute.elem).forEach((arrayAttributeElem, i) => {
        expect(arrayAttributeElem.prop("attrName")).toEqual(attrName);
        expect(arrayAttributeElem.prop("attrType")).toEqual(attrType);
        expect(arrayAttributeElem.prop("attrValue")).toEqual(
          Object.values(attrValue)[0][i]
        );
      });
    }
  });
});
