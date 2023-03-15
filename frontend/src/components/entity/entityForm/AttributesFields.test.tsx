/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React, { FC } from "react";
import { useForm } from "react-hook-form";

import { Schema } from "../EntityFormSchema";

import { AttributesFields } from "./AttributesFields";

import { TestWrapper } from "services/TestWrapper";

test("should render a component with essential props", function () {
  const entity: Schema = {
    name: "hoge",
    note: "fuga",
    isToplevel: false,
    webhooks: [],
    attrs: [],
  };
  const Wrapper: FC = () => {
    const { setValue, control } = useForm<Schema>({
      defaultValues: entity,
    });
    return (
      <AttributesFields
        control={control}
        setValue={setValue}
        referralEntities={[]}
      />
    );
  };

  expect(() => render(<Wrapper />, { wrapper: TestWrapper })).not.toThrow();
});
