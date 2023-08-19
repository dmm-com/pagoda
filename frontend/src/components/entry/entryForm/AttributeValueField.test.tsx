/**
 * @jest-environment jsdom
 */

import { EntryAttributeTypeTypeEnum } from "@dmm-com/airone-apiclient-typescript-fetch";
import { shallow } from "enzyme";
import React from "react";

import { ReactHookFormTestWrapper } from "../../../ReactHookFormTestWrapper";

import { AttributeValueField } from "./AttributeValueField";
import { Schema } from "./EntryFormSchema";

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

const attributes: Array<{
  value: any;
  type: EntryAttributeTypeTypeEnum;
  elem: string;
}> = [
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
    elem: "ElemDate",
  },
  {
    value: { asBoolean: true },
    type: EntryAttributeTypeTypeEnum.BOOLEAN,
    elem: "ElemBool",
  },
  {
    value: { asObject: { id: 100, name: "hoge", checked: false } },
    type: EntryAttributeTypeTypeEnum.OBJECT,
    elem: "ElemReferral",
  },
  {
    value: {
      asNamedObject: { foo: { id: 100, name: "hoge", checked: false } },
    },
    type: EntryAttributeTypeTypeEnum.NAMED_OBJECT,
    elem: "ElemNamedObject",
  },
  {
    value: { asGroup: { id: 100, name: "hoge", checked: false } },
    type: EntryAttributeTypeTypeEnum.GROUP,
    elem: "ElemReferral",
  },
];

const arrayAttributes: Array<{
  value: any;
  type: EntryAttributeTypeTypeEnum;
  elem: string;
}> = [
  {
    value: { asArrayString: ["hoge", "fuga"] },
    type: EntryAttributeTypeTypeEnum.ARRAY_STRING,
    elem: "ElemString",
  },
  {
    value: {
      asArrayObject: [
        { id: 100, name: "hoge", checked: false },
        { id: 200, name: "fuge", checked: false },
      ],
    },
    type: EntryAttributeTypeTypeEnum.ARRAY_OBJECT,
    elem: "ElemReferral",
  },
  {
    value: {
      asArrayNamedObject: [
        { foo: { id: 100, name: "hoge", checked: false } },
        { bar: { id: 200, name: "fuga", checked: false } },
      ],
    },
    type: EntryAttributeTypeTypeEnum.ARRAY_NAMED_OBJECT,
    elem: "ElemNamedObject",
  },
  {
    value: {
      asArrayGroup: [
        { id: 100, name: "hoge", checked: false },
        { id: 200, name: "fuge", checked: false },
      ],
    },
    type: EntryAttributeTypeTypeEnum.ARRAY_GROUP,
    elem: "ElemReferral",
  },
];

/**
 * TODO rethink how to test AttributeValueField. It has no longer complicated logic so it might have simpler tests.
 *
 */
attributes.forEach((attribute) => {
  it.skip("show AttributeValueField " + attribute.type, () => {
    const attrName = "hoge";
    const attrValue = attribute.value;
    const wrapper = shallow(
      <ReactHookFormTestWrapper
        defaultValues={{} as Schema}
        render={({ control, setValue }) => (
          <AttributeValueField
            control={control}
            setValue={setValue}
            type={attribute.type}
            schemaId={9999}
          />
        )}
      />
    );

    expect(wrapper.find(attribute.elem).length).toEqual(1);
    expect(wrapper.find(attribute.elem).prop("attrName")).toEqual(attrName);
    expect(wrapper.find(attribute.elem).prop("attrType")).toEqual(
      attribute.type
    );
    expect(wrapper.find(attribute.elem).prop("attrValue")).toEqual(
      Object.values(attrValue)[0]
    );
  });
});

arrayAttributes.forEach((arrayAttribute) => {
  it.skip("show AttributeValueField " + arrayAttribute.type, () => {
    const attrName = "hoge";
    const attrValue = arrayAttribute.value;
    const wrapper = shallow(
      <ReactHookFormTestWrapper
        defaultValues={{} as Schema}
        render={({ control, setValue }) => (
          <AttributeValueField
            control={control}
            setValue={setValue}
            type={arrayAttribute.type}
            schemaId={9999}
          />
        )}
      />
    );

    if (
      arrayAttribute.type == EntryAttributeTypeTypeEnum.ARRAY_GROUP ||
      arrayAttribute.type == EntryAttributeTypeTypeEnum.ARRAY_OBJECT
    ) {
      expect(wrapper.find(arrayAttribute.elem).length).toEqual(1);
      wrapper.find(arrayAttribute.elem).forEach((arrayAttributeElem) => {
        expect(arrayAttributeElem.prop("attrName")).toEqual(attrName);
        expect(arrayAttributeElem.prop("attrType")).toEqual(
          arrayAttribute.type
        );
      });
    } else {
      expect(wrapper.find(arrayAttribute.elem).length).toEqual(2);
      wrapper.find(arrayAttribute.elem).forEach((arrayAttributeElem, i) => {
        expect(arrayAttributeElem.prop("attrName")).toEqual(attrName);
        expect(arrayAttributeElem.prop("attrType")).toEqual(
          arrayAttribute.type
        );
        expect(arrayAttributeElem.prop("attrValue")).toEqual(
          (Object.values(attrValue)[0] as any)[i]
        );
      });
    }
  });
});
