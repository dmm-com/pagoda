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

it("show string type EditAttributeValue", () => {
  const djangoContext = DjangoContext.getInstance();
  const attrName = "hoge";
  const attrValue = "fuga";
  const wrapper = shallow(
    <EditAttributeValue
      attrName={attrName}
      attrInfo={{
        value: attrValue,
        type: djangoContext.attrTypeValue.string,
      }}
      handleChangeAttribute={mockHandleChangeAttribute}
      handleNarrowDownEntries={mockHandleNarrowDownEntries}
      handleNarrowDownGroups={mockHandleNarrowDownGroups}
      handleClickDeleteListItem={mockHandleClickDeleteListItem}
    />
  );

  expect(wrapper.find("ElemString").length).toEqual(1);
  expect(wrapper.props()).toEqual({
    attrName: attrName,
    attrType: djangoContext.attrTypeValue.string,
    attrValue: attrValue,
    handleChange: mockHandleChangeAttribute,
    handleClickDeleteListItem: mockHandleClickDeleteListItem,
  });
});
