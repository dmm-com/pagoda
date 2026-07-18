/**
 * @jest-environment jsdom
 */

import { EntryAttributeTypeTypeEnum } from "@dmm-com/airone-apiclient-typescript-fetch";
import { fireEvent, render, screen, within } from "@testing-library/react";
import { FC } from "react";
import { useForm } from "react-hook-form";

import { Schema } from "./EntryFormSchema";
import {
  MultiSelectAttributeValueField,
  SelectAttributeValueField,
} from "./SelectAttributeValueField";

import { TestWrapper } from "TestWrapper";

const choices = [
  { value: "first", label: "First choice" },
  { label: "Incomplete choice" },
  { value: "second", label: "Second choice" },
];

const defaultValues: Schema = {
  name: "Entry",
  schema: { id: 1, name: "Entity" },
  attrs: {
    1: {
      index: 0,
      type: EntryAttributeTypeTypeEnum.SELECT,
      isMandatory: false,
      schema: { id: 1, name: "Choice" },
      value: {
        asSelect: { value: "first", label: "Stale first label" },
        asMultiSelect: [
          { value: "second", label: "Stale second label" },
          { value: "removed", label: "Removed choice" },
        ],
      },
    },
  },
};

const FieldHarness: FC<{ multiple?: boolean; disabled?: boolean }> = ({
  multiple = false,
  disabled = false,
}) => {
  const form = useForm<Schema>({ defaultValues });
  return (
    <form data-testid="form">
      {multiple ? (
        <MultiSelectAttributeValueField
          attrId={1}
          control={form.control}
          choices={choices}
          isDisabled={disabled}
        />
      ) : (
        <SelectAttributeValueField
          attrId={1}
          control={form.control}
          choices={choices}
          isDisabled={disabled}
        />
      )}
      <output data-testid="value">
        {JSON.stringify(form.watch("attrs.1.value"))}
      </output>
    </form>
  );
};

describe("SelectAttributeValueField", () => {
  test("renders the selected value and excludes incomplete choices", () => {
    render(<FieldHarness />, { wrapper: TestWrapper });

    expect(screen.getByRole("combobox")).toHaveTextContent("First choice");
    fireEvent.mouseDown(screen.getByRole("combobox"));

    const listbox = screen.getByRole("listbox");
    expect(within(listbox).getByText("First choice")).toBeInTheDocument();
    expect(within(listbox).getByText("Second choice")).toBeInTheDocument();
    expect(
      within(listbox).queryByText("Incomplete choice"),
    ).not.toBeInTheDocument();
  });

  test("stores the canonical value and label after selection", () => {
    render(<FieldHarness />, { wrapper: TestWrapper });

    fireEvent.mouseDown(screen.getByRole("combobox"));
    fireEvent.click(screen.getByRole("option", { name: "Second choice" }));

    expect(screen.getByTestId("value")).toHaveTextContent(
      '"asSelect":{"value":"second","label":"Second choice"}',
    );
  });

  test("stores null when the user selects the empty option", () => {
    render(<FieldHarness />, { wrapper: TestWrapper });

    fireEvent.mouseDown(screen.getByRole("combobox"));
    fireEvent.click(screen.getByRole("option", { name: "未選択" }));

    expect(screen.getByTestId("value")).toHaveTextContent('"asSelect":null');
  });

  test("disables the field", () => {
    render(<FieldHarness disabled />, { wrapper: TestWrapper });

    expect(screen.getByRole("combobox")).toHaveAttribute(
      "aria-disabled",
      "true",
    );
  });
});

describe("MultiSelectAttributeValueField", () => {
  test("refreshes current labels while preserving stale selected values", () => {
    render(<FieldHarness multiple />, { wrapper: TestWrapper });

    expect(screen.getByText("Second choice")).toBeInTheDocument();
    expect(screen.getByText("Removed choice")).toBeInTheDocument();
    expect(screen.getAllByTestId("CancelIcon")).toHaveLength(2);
  });

  test("adds a choice and stores canonical values", () => {
    render(<FieldHarness multiple />, { wrapper: TestWrapper });

    fireEvent.click(screen.getByRole("button", { name: "Open" }));
    fireEvent.click(screen.getByRole("option", { name: "First choice" }));

    expect(screen.getByTestId("value")).toHaveTextContent(
      '"asMultiSelect":[{"value":"second","label":"Second choice"},{"value":"removed","label":"Removed choice"},{"value":"first","label":"First choice"}]',
    );
  });
});
