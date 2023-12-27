/**
 * @jest-environment jsdom
 */

import { zodResolver } from "@hookform/resolvers/zod";
import {
  act,
  fireEvent,
  render,
  renderHook,
  screen,
} from "@testing-library/react";
import React from "react";
import { useForm } from "react-hook-form";

import { schema } from "../../entry/entryForm/EntryFormSchema";

import { BasicFields } from "./BasicFields";
import { Schema } from "./EntityFormSchema";

import { TestWrapper } from "TestWrapper";

describe("BasicFields", () => {
  const defaultValues: Schema = {
    name: "hoge",
    note: "fuga",
    isToplevel: false,
    webhooks: [],
    attrs: [],
  };

  test("should provide basic fields editor", function () {
    const {
      result: {
        current: { control, getValues },
      },
    } = renderHook(() =>
      useForm<Schema>({
        resolver: zodResolver(schema),
        mode: "onBlur",
        defaultValues,
      }),
    );

    render(<BasicFields control={control} />, { wrapper: TestWrapper });

    act(() => {
      fireEvent.change(screen.getByPlaceholderText("エンティティ名"), {
        target: { value: "entity name" },
      });
      fireEvent.change(screen.getByPlaceholderText("備考"), {
        target: { value: "note" },
      });
      screen.getByRole("checkbox").click();
    });

    expect(screen.getByPlaceholderText("エンティティ名")).toHaveValue(
      "entity name",
    );
    expect(screen.getByPlaceholderText("備考")).toHaveValue("note");
    expect(screen.getByRole("checkbox")).toBeChecked();

    expect(getValues("name")).toEqual("entity name");
    expect(getValues("note")).toEqual("note");
    expect(getValues("isToplevel")).toBeTruthy();
  });
});
