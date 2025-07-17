/**
 * @jest-environment jsdom
 */

import { EntryAttributeTypeTypeEnum } from "@dmm-com/airone-apiclient-typescript-fetch";
import { zodResolver } from "@hookform/resolvers/zod";
import { act, screen, render, renderHook } from "@testing-library/react";
import React from "react";
import { useForm } from "react-hook-form";

import { DateTimeAttributeValueField } from "./DateTimeAttributeValueField";
import { schema, Schema } from "./EntryFormSchema";

import { TestWrapper } from "TestWrapper";

import "@testing-library/jest-dom";

describe("DateAttributeValueField", () => {
  const defaultValues: Schema = {
    name: "entry",
    schema: {
      id: 1,
      name: "entity",
    },
    attrs: {
      "0": {
        type: EntryAttributeTypeTypeEnum.DATETIME,
        index: 0,
        isMandatory: false,
        schema: {
          id: 1,
          name: "datetime",
        },
        value: {
          asString: "2020-01-01T00:00:00+00:00",
        },
      },
    },
  };

  test("should provide date value editor", () => {
    const {
      result: {
        current: { control, getValues, setValue },
      },
    } = renderHook(() =>
      useForm<Schema>({
        resolver: zodResolver(schema),
        mode: "onBlur",
        defaultValues,
      }),
    );

    render(
      <DateTimeAttributeValueField
        attrId={0}
        control={control}
        setValue={setValue}
      />,
      {
        wrapper: TestWrapper,
      },
    );

    expect(screen.getByRole("textbox")).toHaveValue("2020/01/01 00:00:00");
    expect(getValues("attrs.0.value.asString")).toEqual(
      "2020-01-01T00:00:00+00:00",
    );

    // Open the date picker
    act(() => {
      screen.getByRole("button").click();
    });
    // Select 2020-01-02
    act(() => {
      screen.getByRole("gridcell", { name: "2" }).click();
    });

    expect(screen.getByRole("textbox")).toHaveValue("2020/01/02 00:00:00");
    expect(getValues("attrs.0.value.asString")).toEqual(
      "2020-01-02T00:00:00.000Z",
    );
  });
});
