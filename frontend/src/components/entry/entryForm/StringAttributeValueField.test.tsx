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
import {
  ArrayStringAttributeValueField,
  StringAttributeValueField,
} from "./StringAttributeValueField";

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
      "0": {
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
      "1": {
        type: EntryAttributeTypeTypeEnum.ARRAY_STRING,
        index: 1,
        isMandatory: false,
        schema: {
          id: 2,
          name: "array-string",
        },
        value: {
          asArrayString: [
            {
              value: "initial value",
            },
          ],
        },
      },
    },
  };

  test("should provide string value editor", async () => {
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

    render(<StringAttributeValueField attrId={0} control={control} />, {
      wrapper: TestWrapper,
    });

    expect(screen.getByRole("textbox")).toHaveValue("initial value");

    act(() => {
      fireEvent.change(screen.getByRole("textbox"), {
        target: { value: "new value" },
      });
    });

    expect(screen.getByRole("textbox")).toHaveValue("new value");

    expect(getValues("attrs.0.value.asString")).toEqual("new value");
  });

  test("should provide array-string value editor", async () => {
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

    render(<ArrayStringAttributeValueField attrId={1} control={control} />, {
      wrapper: TestWrapper,
    });

    // At least 1 element appears even if the initial value is empty
    expect(getValues("attrs.1.value.asArrayString")).toHaveLength(1);
    expect(screen.getAllByRole("textbox")).toHaveLength(1);
    expect(screen.getAllByRole("textbox")[0]).toHaveValue("initial value");

    // Edit the first element
    act(() => {
      fireEvent.change(screen.getAllByRole("textbox")[0], {
        target: { value: "new value" },
      });
    });
    expect(screen.getAllByRole("textbox")[0]).toHaveValue("new value");
    expect(getValues("attrs.1.value.asArrayString")).toEqual([
      { value: "new value" },
    ]);

    // add second element
    act(() => {
      // now there is 1 element, and each element has 2 buttons (delete, add)
      // click the add button of the first element
      screen.getAllByRole("button")[1].click();
    });
    expect(screen.getAllByRole("textbox")).toHaveLength(2);
    expect(screen.getAllByRole("textbox")[0]).toHaveValue("new value");
    expect(screen.getAllByRole("textbox")[1]).toHaveValue("");
    expect(getValues("attrs.1.value.asArrayString")).toEqual([
      { value: "new value" },
      { value: "" },
    ]);

    // delete first element
    act(() => {
      // now there is 1 element, and each element has 2 buttons (delete, add)
      // click the delete button of the first element
      screen.getAllByRole("button")[0].click();
    });
    expect(screen.getAllByRole("textbox")).toHaveLength(1);
    expect(screen.getAllByRole("textbox")[0]).toHaveValue("");
    expect(getValues("attrs.1.value.asArrayString")).toEqual([{ value: "" }]);
  });
});
