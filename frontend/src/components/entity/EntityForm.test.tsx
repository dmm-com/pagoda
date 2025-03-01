/**
 * @jest-environment jsdom
 */

import { zodResolver } from "@hookform/resolvers/zod";
import { render, renderHook, screen } from "@testing-library/react";
import React from "react";
import { useForm } from "react-hook-form";

import { schema } from "../entry/entryForm/EntryFormSchema";

import { Schema } from "./entityForm/EntityFormSchema";

import { TestWrapper } from "TestWrapper";
import { EntityForm } from "components/entity/EntityForm";

describe("EntityForm", () => {
  const entity: Schema = {
    name: "hoge",
    note: "fuga",
    isToplevel: false,
    webhooks: [],
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
});
