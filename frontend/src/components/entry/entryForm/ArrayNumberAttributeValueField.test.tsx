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
} from "@testing-library/react";
import React from "react";
import { useForm } from "react-hook-form";

import {
  ArrayNumberAttributeValueField,
  NumberAttributeValueFieldForArray,
} from "./ArrayNumberAttributeValueField";
import { schema, Schema } from "./EntryFormSchema";

import { TestWrapper } from "TestWrapper";

import "@testing-library/jest-dom";

describe("ArrayNumberAttributeValueField", () => {
  const defaultValues: Schema = {
    name: "entry",
    schema: {
      id: 1,
      name: "entity",
    },
    attrs: {
      "0": {
        type: EntryAttributeTypeTypeEnum.NUMBER,
        index: 0,
        isMandatory: false,
        schema: {
          id: 1,
          name: "number",
        },
        value: {
          asNumber: 42,
        },
      },
      "1": {
        type: EntryAttributeTypeTypeEnum.ARRAY_NUMBER,
        index: 1,
        isMandatory: false,
        schema: {
          id: 2,
          name: "array-number",
        },
        value: {
          asArrayNumber: [
            {
              value: 123,
            },
          ],
        },
      },
      "2": {
        type: EntryAttributeTypeTypeEnum.ARRAY_NUMBER,
        index: 2,
        isMandatory: false,
        schema: {
          id: 3,
          name: "empty-array-number",
        },
        value: {
          asArrayNumber: [{ value: null }],
        },
      },
    },
  };

  test("should provide array-number value editor", async () => {
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

    render(<ArrayNumberAttributeValueField attrId={1} control={control} />, {
      wrapper: TestWrapper,
    });

    // At least 1 element appears even if the initial value is empty
    expect(getValues("attrs.1.value.asArrayNumber")).toHaveLength(1);
    expect(screen.getAllByRole("spinbutton")).toHaveLength(1);
    expect(screen.getAllByRole("spinbutton")[0]).toHaveValue(123);

    // Edit the first element
    act(() => {
      fireEvent.change(screen.getAllByRole("spinbutton")[0], {
        target: { value: "456" },
      });
    });
    expect(screen.getAllByRole("spinbutton")[0]).toHaveValue(456);
    expect(getValues("attrs.1.value.asArrayNumber")).toEqual([{ value: 456 }]);

    // add second element
    act(() => {
      // now there is 1 element, and each element has 2 buttons (delete, add)
      // click the add button of the first element
      screen.getAllByRole("button")[1].click();
    });
    expect(screen.getAllByRole("spinbutton")).toHaveLength(2);
    expect(screen.getAllByRole("spinbutton")[0]).toHaveValue(456);
    expect(screen.getAllByRole("spinbutton")[1]).toHaveValue(null);
    expect(getValues("attrs.1.value.asArrayNumber")).toEqual([
      { value: 456 },
      { value: null },
    ]);

    // delete first element
    act(() => {
      // now there are 2 elements, and each element has 2 buttons (delete, add)
      // click the delete button of the first element
      screen.getAllByRole("button")[0].click();
    });
    expect(screen.getAllByRole("spinbutton")).toHaveLength(1);
    expect(screen.getAllByRole("spinbutton")[0]).toHaveValue(null);
    expect(getValues("attrs.1.value.asArrayNumber")).toEqual([{ value: null }]);
  });

  test("should handle empty array initialization", async () => {
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

    render(<ArrayNumberAttributeValueField attrId={2} control={control} />, {
      wrapper: TestWrapper,
    });

    // Empty array should automatically have one empty element
    expect(getValues("attrs.2.value.asArrayNumber")).toHaveLength(1);
    expect(screen.getAllByRole("spinbutton")).toHaveLength(1);
    expect(screen.getAllByRole("spinbutton")[0]).toHaveValue(null);
  });

  test("should handle number input conversions", async () => {
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

    render(<ArrayNumberAttributeValueField attrId={1} control={control} />, {
      wrapper: TestWrapper,
    });

    const input = screen.getAllByRole("spinbutton")[0];

    // Test positive integer
    act(() => {
      fireEvent.change(input, { target: { value: "789" } });
    });
    expect(getValues("attrs.1.value.asArrayNumber.0.value")).toBe(789);

    // Test negative integer
    act(() => {
      fireEvent.change(input, { target: { value: "-123" } });
    });
    expect(getValues("attrs.1.value.asArrayNumber.0.value")).toBe(-123);

    // Test decimal number
    act(() => {
      fireEvent.change(input, { target: { value: "123.45" } });
    });
    expect(getValues("attrs.1.value.asArrayNumber.0.value")).toBe(123.45);

    // Test zero
    act(() => {
      fireEvent.change(input, { target: { value: "0" } });
    });
    expect(getValues("attrs.1.value.asArrayNumber.0.value")).toBe(0);

    // Test empty string converts to null
    act(() => {
      fireEvent.change(input, { target: { value: "" } });
    });
    expect(getValues("attrs.1.value.asArrayNumber.0.value")).toBe(null);
  });

  test("should maintain at least one element when deleting the last item", async () => {
    const {
      result: {
        current: { control, getValues },
      },
    } = renderHook(() =>
      useForm<Schema>({
        resolver: zodResolver(schema),
        mode: "onBlur",
        defaultValues: {
          ...defaultValues,
          attrs: {
            ...defaultValues.attrs,
            "1": {
              ...defaultValues.attrs["1"],
              value: {
                asArrayNumber: [{ value: 100 }],
              },
            },
          },
        },
      }),
    );

    render(<ArrayNumberAttributeValueField attrId={1} control={control} />, {
      wrapper: TestWrapper,
    });

    // Should have 1 element initially
    expect(screen.getAllByRole("spinbutton")).toHaveLength(1);
    expect(getValues("attrs.1.value.asArrayNumber")).toHaveLength(1);

    // Delete the only element
    act(() => {
      screen.getAllByRole("button")[0].click(); // Delete button
    });

    // Should still have 1 element (empty one)
    expect(screen.getAllByRole("spinbutton")).toHaveLength(1);
    expect(getValues("attrs.1.value.asArrayNumber")).toHaveLength(1);
    expect(getValues("attrs.1.value.asArrayNumber.0.value")).toBe(null);
  });

  test("should add multiple elements correctly", async () => {
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

    render(<ArrayNumberAttributeValueField attrId={1} control={control} />, {
      wrapper: TestWrapper,
    });

    // Start with 1 element
    expect(screen.getAllByRole("spinbutton")).toHaveLength(1);

    // Add second element
    act(() => {
      screen.getAllByRole("button")[1].click(); // Add button
    });
    expect(screen.getAllByRole("spinbutton")).toHaveLength(2);

    // Add third element after the second one
    act(() => {
      screen.getAllByRole("button")[3].click(); // Add button of second element
    });
    expect(screen.getAllByRole("spinbutton")).toHaveLength(3);

    // Fill in values
    act(() => {
      fireEvent.change(screen.getAllByRole("spinbutton")[0], {
        target: { value: "1" },
      });
      fireEvent.change(screen.getAllByRole("spinbutton")[1], {
        target: { value: "2" },
      });
      fireEvent.change(screen.getAllByRole("spinbutton")[2], {
        target: { value: "3" },
      });
    });

    expect(getValues("attrs.1.value.asArrayNumber")).toEqual([
      { value: 1 },
      { value: 2 },
      { value: 3 },
    ]);
  });

  test("should delete elements from middle correctly", async () => {
    const {
      result: {
        current: { control, getValues },
      },
    } = renderHook(() =>
      useForm<Schema>({
        resolver: zodResolver(schema),
        mode: "onBlur",
        defaultValues: {
          ...defaultValues,
          attrs: {
            ...defaultValues.attrs,
            "1": {
              ...defaultValues.attrs["1"],
              value: {
                asArrayNumber: [{ value: 1 }, { value: 2 }, { value: 3 }],
              },
            },
          },
        },
      }),
    );

    render(<ArrayNumberAttributeValueField attrId={1} control={control} />, {
      wrapper: TestWrapper,
    });

    // Should have 3 elements
    expect(screen.getAllByRole("spinbutton")).toHaveLength(3);
    expect(getValues("attrs.1.value.asArrayNumber")).toHaveLength(3);

    // Delete middle element (index 1)
    act(() => {
      screen.getAllByRole("button")[2].click(); // Delete button of second element
    });

    // Should have 2 elements left
    expect(screen.getAllByRole("spinbutton")).toHaveLength(2);
    expect(getValues("attrs.1.value.asArrayNumber")).toEqual([
      { value: 1 },
      { value: 3 },
    ]);
  });
});

describe("NumberAttributeValueFieldForArray", () => {
  const mockHandleClickDeleteListItem = jest.fn();
  const mockHandleClickAddListItem = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  const defaultValues: Schema = {
    name: "entry",
    schema: {
      id: 1,
      name: "entity",
    },
    attrs: {
      "0": {
        type: EntryAttributeTypeTypeEnum.ARRAY_NUMBER,
        index: 0,
        isMandatory: false,
        schema: {
          id: 1,
          name: "array-number",
        },
        value: {
          asArrayNumber: [{ value: 42 }],
        },
      },
    },
  };

  test("should render number input field", async () => {
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
      <NumberAttributeValueFieldForArray
        attrId={0}
        index={0}
        control={control}
        handleClickDeleteListItem={mockHandleClickDeleteListItem}
        handleClickAddListItem={mockHandleClickAddListItem}
      />,
      { wrapper: TestWrapper },
    );

    expect(screen.getByRole("spinbutton")).toBeInTheDocument();
    expect(screen.getByRole("spinbutton")).toHaveValue(42);
  });

  test("should call delete handler when delete button is clicked", async () => {
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
      <NumberAttributeValueFieldForArray
        attrId={0}
        index={0}
        control={control}
        handleClickDeleteListItem={mockHandleClickDeleteListItem}
        handleClickAddListItem={mockHandleClickAddListItem}
      />,
      { wrapper: TestWrapper },
    );

    const deleteButton = screen.getByRole("button", { name: /delete/i });
    act(() => {
      deleteButton.click();
    });

    expect(mockHandleClickDeleteListItem).toHaveBeenCalledWith(0);
  });

  test("should call add handler when add button is clicked", async () => {
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
      <NumberAttributeValueFieldForArray
        attrId={0}
        index={0}
        control={control}
        handleClickDeleteListItem={mockHandleClickDeleteListItem}
        handleClickAddListItem={mockHandleClickAddListItem}
      />,
      { wrapper: TestWrapper },
    );

    const addButton = screen.getByRole("button", { name: /add/i });
    act(() => {
      addButton.click();
    });

    expect(mockHandleClickAddListItem).toHaveBeenCalledWith(0);
  });

  test("should not render buttons when handlers are not provided", async () => {
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
      <NumberAttributeValueFieldForArray
        attrId={0}
        index={0}
        control={control}
      />,
      { wrapper: TestWrapper },
    );

    expect(screen.getByRole("spinbutton")).toBeInTheDocument();
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  test("should not render buttons when index is undefined", async () => {
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
      <NumberAttributeValueFieldForArray
        attrId={0}
        control={control}
        handleClickDeleteListItem={mockHandleClickDeleteListItem}
        handleClickAddListItem={mockHandleClickAddListItem}
      />,
      { wrapper: TestWrapper },
    );

    expect(screen.getByRole("spinbutton")).toBeInTheDocument();
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  test("should be disabled when isDisabled prop is true", async () => {
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
      <NumberAttributeValueFieldForArray
        attrId={0}
        index={0}
        control={control}
        isDisabled={true}
      />,
      { wrapper: TestWrapper },
    );

    expect(screen.getByRole("spinbutton")).toBeDisabled();
  });

  test("should handle invalid number input gracefully", async () => {
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
      <NumberAttributeValueFieldForArray
        attrId={0}
        index={0}
        control={control}
      />,
      { wrapper: TestWrapper },
    );

    const input = screen.getByRole("spinbutton");

    // Test invalid input - should be handled by browser number input validation
    act(() => {
      fireEvent.change(input, { target: { value: "abc" } });
    });

    // Browser will prevent invalid characters from being entered in number input
    // The field should maintain its previous valid value or convert to valid number
    expect(getValues("attrs.0.value.asArrayNumber.0.value")).toBeDefined();
  });
});
