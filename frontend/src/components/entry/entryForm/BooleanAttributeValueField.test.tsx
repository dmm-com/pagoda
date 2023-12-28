/**
 * @jest-environment jsdom
 */

import { EntryAttributeTypeTypeEnum } from "@dmm-com/airone-apiclient-typescript-fetch";
import { zodResolver } from "@hookform/resolvers/zod";
import { act, screen, render, renderHook } from "@testing-library/react";
import React from "react";
import { useForm } from "react-hook-form";

import { BooleanAttributeValueField } from "./BooleanAttributeValueField";
import { schema, Schema } from "./EntryFormSchema";

import { TestWrapper } from "TestWrapper";

import "@testing-library/jest-dom";

describe("BooleanAttributeValueField", () => {
  const defaultValues: Schema = {
    name: "entry",
    schema: {
      id: 1,
      name: "entity",
    },
    attrs: {
      "0": {
        type: EntryAttributeTypeTypeEnum.BOOLEAN,
        index: 0,
        isMandatory: false,
        schema: {
          id: 1,
          name: "boolean",
        },
        value: {
          asBoolean: false,
        },
      },
    },
  };

  test("should provide boolean value editor", () => {
    const {
      result: {
        current: { control, getValues },
      },
    } = renderHook(() =>
      useForm<Schema>({
        resolver: zodResolver(schema),
        mode: "onBlur",
        defaultValues,
      })
    );

    render(<BooleanAttributeValueField attrId={0} control={control} />, {
      wrapper: TestWrapper,
    });

    expect(screen.getByRole("checkbox")).not.toBeChecked();

    act(() => {
      screen.getByRole("checkbox").click();
    });

    expect(screen.getByRole("checkbox")).toBeChecked();

    expect(getValues("attrs.0.value.asBoolean")).toEqual(true);
  });
});
