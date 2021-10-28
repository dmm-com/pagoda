/**
 * @jest-environment jsdom
 */

import { shallow, mount } from "enzyme";
import React from "react";

import { DjangoContext } from "../../utils/DjangoContext";

import { AttributeValue, ElemString, ElemObject } from "./AttributeValue.js";

const attrTypeValue = {
  string: 2,
  object: 1,
  named_object: 2049,
  array_object: 1025,
  array_string: 1026,
  array_named_object: 3073,
  array_group: 1040,
  text: 4,
  boolean: 8,
  group: 16,
  date: 32,
};

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

it("show string type AttributeValue", () => {
  const attrValue = "hoge";
  const wrapper = shallow(
    <AttributeValue
      attrName={"attr"}
      attrInfo={{
        value: attrValue,
        type: attrTypeValue.string,
      }}
    />
  );

  expect(wrapper.find("ElemString").length).toEqual(1);
  expect(wrapper.props()).toEqual({ attrValue: attrValue });
});

it("show object type AttributeValue", () => {
  const attrValue = { id: 100, name: "hoge" };
  const wrapper = shallow(
    <AttributeValue
      attrName={"attr"}
      attrInfo={{
        value: attrValue,
        type: attrTypeValue.object,
      }}
    />
  );

  expect(wrapper.find("ElemObject").length).toEqual(1);
  expect(wrapper.props()).toEqual({ attrValue: attrValue });
});
