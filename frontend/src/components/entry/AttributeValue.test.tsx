/**
 * @jest-environment jsdom
 */

import { shallow } from "enzyme";
import React from "react";

import { DjangoContext } from "../../utils/DjangoContext";

import { AttributeValue } from "./AttributeValue";

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
  const djangoContext = DjangoContext.getInstance();
  const attrValue = "hoge";
  const wrapper = shallow(
    <AttributeValue
      attrInfo={{
        value: attrValue,
        type: djangoContext.attrTypeValue.string,
      }}
    />
  );

  expect(wrapper.find("ElemString").length).toEqual(1);
  expect(wrapper.props()).toEqual({ attrValue: attrValue });
});

it("show object type AttributeValue", () => {
  const djangoContext = DjangoContext.getInstance();
  const attrValue = { id: 100, name: "hoge" };
  const wrapper = shallow(
    <AttributeValue
      attrInfo={{
        value: attrValue,
        type: djangoContext.attrTypeValue.object,
      }}
    />
  );

  expect(wrapper.find("ElemObject").length).toEqual(1);
  expect(wrapper.props()).toEqual({ attrValue: attrValue });
});
