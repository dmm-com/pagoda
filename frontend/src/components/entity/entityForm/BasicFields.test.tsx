/**
 */

import { zodResolver } from "@hookform/resolvers/zod";
import {
  act,
  fireEvent,
  render,
  renderHook,
  screen,
} from "@testing-library/react";
import { useForm } from "react-hook-form";

import { schema } from "../../entry/entryForm/EntryFormSchema";

import { BasicFields } from "./BasicFields";
import { Schema } from "./EntityFormSchema";

import { TestWrapper } from "TestWrapper";
import i18n from "i18n/config";

describe("BasicFields", () => {
  const defaultValues: Schema = {
    name: "hoge",
    note: "fuga",
    itemNamePattern: "",
    itemNameType: "US",
    isToplevel: false,
    webhooks: [],
    isolationRules: [],
    deleteChainExcludeEntities: [],
    attrs: [],
  };

  test("should provide basic fields editor", function () {
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

    render(<BasicFields control={control} setValue={setValue} />, {
      wrapper: TestWrapper,
    });

    act(() => {
      fireEvent.change(screen.getByPlaceholderText("モデル名"), {
        target: { value: "entity name" },
      });
      fireEvent.change(screen.getByPlaceholderText("備考"), {
        target: { value: "note" },
      });
      screen.getByRole("checkbox").click();
    });

    expect(screen.getByPlaceholderText("モデル名")).toHaveValue("entity name");
    expect(screen.getByPlaceholderText("備考")).toHaveValue("note");
    expect(screen.getByRole("checkbox")).toBeChecked();

    expect(getValues("name")).toEqual("entity name");
    expect(getValues("note")).toEqual("note");
    expect(getValues("isToplevel")).toBeTruthy();
  });

  test("should render in English", async () => {
    await act(async () => {
      await i18n.changeLanguage("en");
    });

    const {
      result: {
        current: { control, setValue },
      },
    } = renderHook(() =>
      useForm<Schema>({
        resolver: zodResolver(schema),
        mode: "onBlur",
        defaultValues,
      }),
    );

    render(<BasicFields control={control} setValue={setValue} />, {
      wrapper: TestWrapper,
    });

    expect(screen.getByText("Basic information")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Entity name")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Notes")).toBeInTheDocument();
  });
});
