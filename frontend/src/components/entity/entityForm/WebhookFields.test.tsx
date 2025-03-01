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

import { Schema } from "./EntityFormSchema";
import { WebhookFields } from "./WebhookFields";

import { TestWrapper } from "TestWrapper";

describe("WebhookFields", () => {
  const defaultValues: Schema = {
    name: "hoge",
    note: "fuga",
    isToplevel: false,
    webhooks: [],
    attrs: [],
  };

  test("should provide webhook fields editor", () => {
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

    render(<WebhookFields control={control} />, { wrapper: TestWrapper });

    expect(screen.queryAllByPlaceholderText("URL")).toHaveLength(0);

    // add first webhook
    act(() => {
      screen.getByRole("button").click();
    });

    expect(screen.queryAllByPlaceholderText("URL")).toHaveLength(1);

    // edit first webhook
    act(() => {
      fireEvent.change(screen.getByPlaceholderText("URL"), {
        target: { value: "https://example.com/" },
      });
      fireEvent.change(screen.getByPlaceholderText("ラベル"), {
        target: { value: "label" },
      });
      screen.getByRole("checkbox").click();
    });

    expect(screen.getByPlaceholderText("URL")).toHaveValue(
      "https://example.com/",
    );
    expect(screen.getByPlaceholderText("ラベル")).toHaveValue("label");
    expect(screen.getByRole("checkbox")).toBeChecked();
    expect(getValues("webhooks.0.url")).toEqual("https://example.com/");
    expect(getValues("webhooks.0.label")).toEqual("label");
    expect(getValues("webhooks.0.isEnabled")).toBeTruthy();

    // add second webhook
    act(() => {
      // now there is 1 webhook, and each webhook has 3 buttons (headers, delete, add)
      // click the add button of the first webhook
      screen.getAllByRole("button")[2].click();
    });

    expect(screen.queryAllByPlaceholderText("URL")).toHaveLength(2);

    // delete first webhook
    act(() => {
      // now there is 2 webhook, and each webhook has 3 buttons (headers, delete, add)
      // click the delete button of the first webhook
      screen.getAllByRole("button")[1].click();
    });

    expect(screen.queryAllByPlaceholderText("URL")).toHaveLength(1);

    expect(screen.getByPlaceholderText("URL")).toHaveValue("");
    expect(screen.getByPlaceholderText("ラベル")).toHaveValue("");
    expect(screen.getByRole("checkbox")).not.toBeChecked();

    expect(getValues("webhooks.0.url")).toEqual("");
    expect(getValues("webhooks.0.label")).toEqual("");
    expect(getValues("webhooks.0.isEnabled")).toBeFalsy();
  });
});
