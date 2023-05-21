/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React, { FC } from "react";
import { useForm } from "react-hook-form";

import { Schema } from "../EntityFormSchema";

import { BasicFields } from "./BasicFields";

import { TestWrapper } from "TestWrapper";

test("should render a component with essential props", function () {
  const entity: Schema = {
    name: "hoge",
    note: "fuga",
    isToplevel: false,
    webhooks: [],
    attrs: [],
  };
  const Wrapper: FC = () => {
    const { control } = useForm<Schema>({
      defaultValues: entity,
    });
    return <BasicFields control={control} />;
  };

  expect(() => render(<Wrapper />, { wrapper: TestWrapper })).not.toThrow();
});
