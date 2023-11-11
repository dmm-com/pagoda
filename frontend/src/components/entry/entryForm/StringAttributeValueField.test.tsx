/**
 * @jest-environment jsdom
 */

import { EntryAttributeTypeTypeEnum } from "@dmm-com/airone-apiclient-typescript-fetch";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  act,
  fireEvent,
  screen,
  render,
  renderHook,
} from "@testing-library/react";
import React from "react";
import { useForm } from "react-hook-form";

import { schema, Schema } from "./EntryFormSchema";
import { StringAttributeValueField } from "./StringAttributeValueField";

import { TestWrapper } from "TestWrapper";

import "@testing-library/jest-dom";

describe("StringAttributeValueField", () => {
  const defaultValues: Schema = {
    name: "entry",
    schema: {
      id: 1,
      name: "entity",
    },
    attrs: {
      string: {
        type: EntryAttributeTypeTypeEnum.STRING,
        index: 0,
        isMandatory: false,
        schema: {
          id: 1,
          name: "string",
        },
        value: {
          asString: "initial value",
        },
      },
    },
  };

  test("should provide string value editor", async () => {
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

    render(<StringAttributeValueField attrId={0} control={control} />, {
      wrapper: TestWrapper,
    });

    // TODO check if the initial value is rendered

    act(() => {
      fireEvent.change(screen.getByRole("textbox"), {
        target: { value: "new value" },
      });
    });

    expect(screen.getByRole("textbox")).toHaveValue("new value");
  });
});
