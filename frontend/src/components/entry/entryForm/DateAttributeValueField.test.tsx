/**
 * @jest-environment jsdom
 */

import { EntryAttributeTypeTypeEnum } from "@dmm-com/airone-apiclient-typescript-fetch";
import { zodResolver } from "@hookform/resolvers/zod";
import { act, screen, render, renderHook } from "@testing-library/react";
import React from "react";
import { useForm } from "react-hook-form";

import { DateAttributeValueField } from "./DateAttributeValueField";
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
        type: EntryAttributeTypeTypeEnum.DATE,
        index: 0,
        isMandatory: false,
        schema: {
          id: 1,
          name: "date",
        },
        value: {
          asString: "2020-01-01",
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
      })
    );

    render(
      <DateAttributeValueField
        attrId={0}
        control={control}
        setValue={setValue}
      />,
      {
        wrapper: TestWrapper,
      }
    );

    expect(screen.getByRole("textbox")).toHaveValue("2020/01/01");
    expect(getValues("attrs.0.value.asString")).toEqual("2020-01-01");

    // Open the date picker
    act(() => {
      screen.getByRole("button").click();
    });
    // Select 2020-01-02
    act(() => {
      screen.getByRole("gridcell", { name: "2" }).click();
    });

    expect(screen.getByRole("textbox")).toHaveValue("2020/01/02");
    expect(getValues("attrs.0.value.asString")).toEqual("2020-1-2");
  });
});
