/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React, { FC } from "react";
import { useForm } from "react-hook-form";

import { Schema } from "./entryForm/EntryFormSchema";

import { EntryForm } from "components/entry/EntryForm";
import { TestWrapper } from "services/TestWrapper";

test("should render a component with essential props", function () {
  const entryInfo = { name: "test entry", attrs: {} };
  const setEntryInfo = () => {
    /* do nothing */
  };
  const setIsAnchorLink = () => {
    /* do nothing */
  };

  const Wrapper: FC = () => {
    const { control, setValue } = useForm<Schema>({
      defaultValues: entryInfo,
    });
    return (
      <EntryForm
        entryInfo={entryInfo}
        setEntryInfo={setEntryInfo}
        setIsAnchorLink={setIsAnchorLink}
        control={control}
        setValue={setValue}
      />
    );
  };

  expect(() =>
    render(<Wrapper />, {
      wrapper: TestWrapper,
    })
  ).not.toThrow();
});
