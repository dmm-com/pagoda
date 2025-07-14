/**
 * @jest-environment jsdom
 */

import { EntryAttributeTypeTypeEnum } from "@dmm-com/airone-apiclient-typescript-fetch";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  act,
  fireEvent,
  render,
  renderHook,
  screen,
  waitFor,
} from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import React from "react";
import { useForm } from "react-hook-form";

import { TestWrapper } from "../../../TestWrapper";

import { AttributeValueField } from "./AttributeValueField";
import { schema, Schema } from "./EntryFormSchema";

const server = setupServer(
  http.get("http://localhost/entry/api/v2/*/attr_referrals/", () => {
    return HttpResponse.json([]);
  }),
  http.get("http://localhost/group/api/v2/groups", () => {
    return HttpResponse.json({ count: 0, results: [] });
  }),
  http.get("http://localhost/role/api/v2/", () => {
    return HttpResponse.json([]);
  }),
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe("Array Number Integration Tests", () => {
  const createDefaultValues = (
    numberValue: number | null = null,
    arrayNumberValues: Array<{ value: number | null }> = [{ value: null }],
  ): Schema => ({
    name: "test-entry",
    schema: {
      id: 1,
      name: "test-entity",
    },
    attrs: {
      "1": {
        type: EntryAttributeTypeTypeEnum.NUMBER,
        index: 0,
        isMandatory: false,
        schema: {
          id: 1,
          name: "number_field",
        },
        value: {
          asNumber: numberValue,
        },
      },
      "2": {
        type: EntryAttributeTypeTypeEnum.ARRAY_NUMBER,
        index: 1,
        isMandatory: false,
        schema: {
          id: 2,
          name: "array_number_field",
        },
        value: {
          asArrayNumber: arrayNumberValues,
        },
      },
      "3": {
        type: EntryAttributeTypeTypeEnum.ARRAY_NUMBER,
        index: 2,
        isMandatory: true,
        schema: {
          id: 3,
          name: "mandatory_array_number_field",
        },
        value: {
          asArrayNumber: [{ value: 42 }],
        },
      },
    },
  });

  test("complete user workflow: create, edit, and validate array number entries", async () => {
    const defaultValues = createDefaultValues();

    const {
      result: {
        current: { control, getValues, trigger },
      },
    } = renderHook(() =>
      useForm<Schema>({
        resolver: zodResolver(schema),
        mode: "onBlur",
        defaultValues,
      }),
    );

    // Render both number and array number fields
    render(
      <div>
        <div data-testid="number-field">
          <AttributeValueField
            control={control}
            setValue={() => {}}
            type={EntryAttributeTypeTypeEnum.NUMBER}
            schemaId={1}
          />
        </div>
        <div data-testid="array-number-field">
          <AttributeValueField
            control={control}
            setValue={() => {}}
            type={EntryAttributeTypeTypeEnum.ARRAY_NUMBER}
            schemaId={2}
          />
        </div>
        <div data-testid="mandatory-array-number-field">
          <AttributeValueField
            control={control}
            setValue={() => {}}
            type={EntryAttributeTypeTypeEnum.ARRAY_NUMBER}
            schemaId={3}
          />
        </div>
      </div>,
      { wrapper: TestWrapper },
    );

    // Verify initial state
    expect(screen.getAllByRole("spinbutton")).toHaveLength(3); // 1 number + 1 array number + 1 mandatory

    // Test single number field
    const numberInput = screen.getAllByRole("spinbutton")[0];
    act(() => {
      fireEvent.change(numberInput, { target: { value: "123.45" } });
    });
    expect(getValues("attrs.1.value.asNumber")).toBe(123.45);

    // Test array number field - edit first element
    const arrayNumberInput = screen.getAllByRole("spinbutton")[1];
    act(() => {
      fireEvent.change(arrayNumberInput, { target: { value: "456.78" } });
    });
    expect(getValues("attrs.2.value.asArrayNumber.0.value")).toBe(456.78);

    // Add second element to array
    const addButtons = screen
      .getAllByRole("button")
      .filter((btn) => btn.getAttribute("id") === "add_button");
    act(() => {
      addButtons[0].click();
    });

    // Should now have 4 total spinbutton inputs
    await waitFor(() => {
      expect(screen.getAllByRole("spinbutton")).toHaveLength(4);
    });

    // Fill in the new element
    const newArrayElement = screen.getAllByRole("spinbutton")[2];
    act(() => {
      fireEvent.change(newArrayElement, { target: { value: "789" } });
    });

    expect(getValues("attrs.2.value.asArrayNumber")).toEqual([
      { value: 456.78 },
      { value: 789 },
    ]);

    // Test deletion - remove first element
    const deleteButtons = screen
      .getAllByRole("button")
      .filter((btn) => btn.getAttribute("id") === "del_button");
    act(() => {
      deleteButtons[0].click();
    });

    await waitFor(() => {
      expect(getValues("attrs.2.value.asArrayNumber")).toEqual([
        { value: 789 },
      ]);
    });

    await act(async () => {
      expect(await trigger()).toBe(true);
    });
  });

  test("validation workflow: mandatory field validation", async () => {
    // Start with empty mandatory array
    const defaultValues = createDefaultValues(null, []);
    defaultValues.attrs["3"].value.asArrayNumber = [{ value: null }];

    const {
      result: {
        current: { control, getValues, trigger },
      },
    } = renderHook(() =>
      useForm<Schema>({
        resolver: zodResolver(schema),
        mode: "onBlur",
        defaultValues,
      }),
    );

    render(
      <div data-testid="mandatory-array-number-field">
        <AttributeValueField
          control={control}
          setValue={() => {}}
          type={EntryAttributeTypeTypeEnum.ARRAY_NUMBER}
          schemaId={3}
        />
      </div>,
      { wrapper: TestWrapper },
    );

    // Should have one empty element (auto-created)
    expect(screen.getAllByRole("spinbutton")).toHaveLength(1);
    expect(getValues("attrs.3.value.asArrayNumber.0.value")).toBe(null);

    // Trigger validation - should fail because mandatory field has only null values
    await act(async () => {
      expect(await trigger()).toBe(false);
    });

    // Add a value to make it valid
    const input = screen.getByRole("spinbutton");
    act(() => {
      fireEvent.change(input, { target: { value: "42" } });
    });

    await act(async () => {
      expect(await trigger()).toBe(true);
    });
  });

  test("edge cases: extreme values and special scenarios", async () => {
    const defaultValues = createDefaultValues();

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

    render(
      <div data-testid="array-number-field">
        <AttributeValueField
          control={control}
          setValue={() => {}}
          type={EntryAttributeTypeTypeEnum.ARRAY_NUMBER}
          schemaId={2}
        />
      </div>,
      { wrapper: TestWrapper },
    );

    const input = screen.getByRole("spinbutton");

    // Test extreme values
    const testValues = [
      { input: "0", expected: 0 },
      { input: "-0", expected: -0 },
      { input: "123.456789", expected: 123.456789 },
      { input: "-999.999", expected: -999.999 },
      { input: "1e6", expected: 1000000 },
      { input: "1.23e-4", expected: 0.000123 },
    ];

    for (const { input: inputValue, expected } of testValues) {
      act(() => {
        fireEvent.change(input, { target: { value: inputValue } });
      });
      expect(getValues("attrs.2.value.asArrayNumber.0.value")).toBe(expected);
    }

    // Test empty string conversion to null
    act(() => {
      fireEvent.change(input, { target: { value: "" } });
    });
    expect(getValues("attrs.2.value.asArrayNumber.0.value")).toBe(null);
  });

  test("complex array manipulation workflow", async () => {
    const defaultValues = createDefaultValues(null, [
      { value: 1 },
      { value: 2 },
      { value: 3 },
    ]);

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

    render(
      <div data-testid="array-number-field">
        <AttributeValueField
          control={control}
          setValue={() => {}}
          type={EntryAttributeTypeTypeEnum.ARRAY_NUMBER}
          schemaId={2}
        />
      </div>,
      { wrapper: TestWrapper },
    );

    // Should have 3 initial elements
    expect(screen.getAllByRole("spinbutton")).toHaveLength(3);
    expect(getValues("attrs.2.value.asArrayNumber")).toEqual([
      { value: 1 },
      { value: 2 },
      { value: 3 },
    ]);

    // Insert new element after first one
    const addButtons = screen
      .getAllByRole("button")
      .filter((btn) => btn.getAttribute("id") === "add_button");
    act(() => {
      addButtons[0].click(); // Add after first element
    });

    await waitFor(() => {
      expect(screen.getAllByRole("spinbutton")).toHaveLength(4);
    });

    // Fill the new element with value
    const newInput = screen.getAllByRole("spinbutton")[1];
    act(() => {
      fireEvent.change(newInput, { target: { value: "1.5" } });
    });

    expect(getValues("attrs.2.value.asArrayNumber")).toEqual([
      { value: 1 },
      { value: 1.5 },
      { value: 2 },
      { value: 3 },
    ]);

    // Delete the middle element (index 2, value 2)
    const deleteButtons = screen
      .getAllByRole("button")
      .filter((btn) => btn.getAttribute("id") === "del_button");
    act(() => {
      deleteButtons[2].click();
    });

    await waitFor(() => {
      expect(getValues("attrs.2.value.asArrayNumber")).toEqual([
        { value: 1 },
        { value: 1.5 },
        { value: 3 },
      ]);
    });

    // Verify we still have 3 elements
    expect(screen.getAllByRole("spinbutton")).toHaveLength(3);
  });

  test("accessibility and user experience", async () => {
    const defaultValues = createDefaultValues();

    const {
      result: {
        current: { control },
      },
    } = renderHook(() =>
      useForm<Schema>({
        resolver: zodResolver(schema),
        mode: "onBlur",
        defaultValues,
      }),
    );

    render(
      <div data-testid="array-number-field">
        <AttributeValueField
          control={control}
          setValue={() => {}}
          type={EntryAttributeTypeTypeEnum.ARRAY_NUMBER}
          schemaId={2}
        />
      </div>,
      { wrapper: TestWrapper },
    );

    // Check that inputs have correct type and accessibility attributes
    const numberInputs = screen.getAllByRole("spinbutton");
    numberInputs.forEach((input) => {
      expect(input).toHaveAttribute("type", "number");
      expect(input).toBeEnabled();
    });

    // Check that buttons are properly labeled and functional
    const addButtons = screen
      .getAllByRole("button")
      .filter((btn) => btn.getAttribute("id") === "add_button");
    const deleteButtons = screen
      .getAllByRole("button")
      .filter((btn) => btn.getAttribute("id") === "del_button");

    expect(addButtons).toHaveLength(1);
    expect(deleteButtons).toHaveLength(1);

    // Buttons should be clickable
    addButtons.forEach((button) => {
      expect(button).toBeEnabled();
    });
    deleteButtons.forEach((button) => {
      expect(button).toBeEnabled();
    });
  });
});
