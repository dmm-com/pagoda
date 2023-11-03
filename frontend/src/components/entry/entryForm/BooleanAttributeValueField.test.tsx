/**
 * @jest-environment jsdom
 */

import { EntryAttributeTypeTypeEnum } from "@dmm-com/airone-apiclient-typescript-fetch";
import { zodResolver } from "@hookform/resolvers/zod";
import { act, render, renderHook } from "@testing-library/react";
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
      boolean: {
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
        current: { control },
      },
    } = renderHook(() =>
      useForm<Schema>({
        resolver: zodResolver(schema),
        mode: "onBlur",
        defaultValues,
      })
    );

    const rendered = render(
      <BooleanAttributeValueField attrId={0} control={control} />,
      { wrapper: TestWrapper }
    );

    expect(rendered.getByRole("checkbox")).not.toBeChecked();

    act(() => {
      rendered.getByRole("checkbox").click();
    });

    expect(rendered.getByRole("checkbox")).toBeChecked();
  });
});
