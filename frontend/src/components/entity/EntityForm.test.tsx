/**
 */

import { zodResolver } from "@hookform/resolvers/zod";
import { act, render, renderHook, screen } from "@testing-library/react";
import { useForm } from "react-hook-form";

import { schema } from "../entry/entryForm/EntryFormSchema";

import { Schema } from "./entityForm/EntityFormSchema";

import { TestWrapper } from "TestWrapper";
import { EntityForm } from "components/entity/EntityForm";
import i18n from "i18n/config";

describe("EntityForm", () => {
  const entity: Schema = {
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

  test("should render a component with essential props", function () {
    const {
      result: {
        current: { control, setValue },
      },
    } = renderHook(() =>
      useForm<Schema>({
        resolver: zodResolver(schema),
        mode: "onBlur",
        defaultValues: entity,
      }),
    );

    render(
      <EntityForm
        control={control}
        setValue={setValue}
        referralEntities={[]}
      />,
      { wrapper: TestWrapper },
    );

    expect(screen.queryByText("基本情報")).toBeInTheDocument();
    expect(screen.queryByText("Webhook")).toBeInTheDocument();
    expect(screen.queryByText("属性情報")).toBeInTheDocument();
  });

  test("should now show webhook fields if its disabled", function () {
    Object.defineProperty(window, "django_context", {
      value: {
        flags: {
          webhook: false,
        },
      },
    });

    const {
      result: {
        current: { control, setValue },
      },
    } = renderHook(() =>
      useForm<Schema>({
        resolver: zodResolver(schema),
        mode: "onBlur",
        defaultValues: entity,
      }),
    );

    render(
      <EntityForm
        control={control}
        setValue={setValue}
        referralEntities={[]}
      />,
      { wrapper: TestWrapper },
    );

    expect(screen.queryByText("基本情報")).toBeInTheDocument();
    expect(screen.queryByText("Webhook")).not.toBeInTheDocument();
    expect(screen.queryByText("属性情報")).toBeInTheDocument();
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
        defaultValues: entity,
      }),
    );

    render(
      <EntityForm
        control={control}
        setValue={setValue}
        referralEntities={[]}
      />,
      { wrapper: TestWrapper },
    );

    expect(screen.queryByText("Basic information")).toBeInTheDocument();
    expect(screen.queryByText("Attribute information")).toBeInTheDocument();
  });
});
