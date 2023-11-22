/**
 * @jest-environment jsdom
 */

import {
  EntryAttributeTypeTypeEnum,
  GetEntryAttrReferral,
} from "@dmm-com/airone-apiclient-typescript-fetch";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  act,
  screen,
  render,
  renderHook,
  within,
} from "@testing-library/react";
import React from "react";
import { useForm } from "react-hook-form";

import { schema, Schema } from "./EntryFormSchema";
import { ObjectAttributeValueField } from "./ObjectAttributeValueField";

import { TestWrapper } from "TestWrapper";

import "@testing-library/jest-dom";

describe("ObjectAttributeValueField", () => {
  const defaultValues: Schema = {
    name: "entry",
    schema: {
      id: 1,
      name: "entity",
    },
    attrs: {
      role: {
        type: EntryAttributeTypeTypeEnum.OBJECT,
        index: 0,
        isMandatory: false,
        schema: {
          id: 1,
          name: "object",
        },
        value: {
          asObject: { id: 1, name: "entry1" },
        },
      },
      arrayObject: {
        type: EntryAttributeTypeTypeEnum.ARRAY_OBJECT,
        index: 1,
        isMandatory: false,
        schema: {
          id: 2,
          name: "array-object",
        },
        value: {
          asArrayObject: [],
        },
      },
    },
  };

  const entries: GetEntryAttrReferral[] = [
    {
      id: 1,
      name: "entry1",
    },
    {
      id: 2,
      name: "entry2",
    },
  ];

  test("should provide object value editor", async () => {
    const {
      result: {
        current: { control, setValue, getValues },
      },
    } = renderHook(() =>
      useForm<Schema>({
        resolver: zodResolver(schema),
        mode: "onBlur",
        defaultValues,
      })
    );

    /* eslint-disable */
    jest
      .spyOn(
        require("../../../repository/AironeApiClientV2").aironeApiClientV2,
        "getEntryAttrReferrals"
      )
      .mockResolvedValue(Promise.resolve(entries));
    /* eslint-enable */

    await act(async () => {
      render(
        <ObjectAttributeValueField
          attrId={0}
          control={control}
          setValue={setValue}
        />,
        { wrapper: TestWrapper }
      );
    });

    // TODO check the initial value, then trigger the change event and check the new value

    // Open the select options
    act(() => {
      screen.getByRole("button", { name: "Open" }).click();
    });
    // Select "role2" element
    act(() => {
      within(screen.getByRole("presentation")).getByText("entry2").click();
    });

    expect(screen.getByRole("combobox")).toHaveValue("entry2");

    expect(getValues("attrs.0.value.asObject")).toEqual({
      id: 2,
      name: "entry2",
      _boolean: false,
    });
  });

  // TODO test array-object
  // TODO test named-object
  // TODO test array-named-object
});
