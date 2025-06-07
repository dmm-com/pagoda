/**
 * @jest-environment jsdom
 */

import {
  EntryAttributeTypeTypeEnum,
  EntityDetail,
} from "@dmm-com/airone-apiclient-typescript-fetch";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  act,
  fireEvent,
  render,
  renderHook,
  screen,
  waitFor,
} from "@testing-library/react";
import React, { FC } from "react";
import { useForm } from "react-hook-form";

import { Schema, schema } from "./entryForm/EntryFormSchema";

import { TestWrapper } from "TestWrapper";
import { EntryForm } from "components/entry/EntryForm";

describe("EntryForm", () => {
  const mockEntity: EntityDetail = {
    id: 2,
    name: "test-entity",
    note: "",
    isToplevel: false,
    hasOngoingChanges: false,
    attrs: [
      {
        id: 1,
        name: "required-string",
        type: EntryAttributeTypeTypeEnum.STRING,
        index: 0,
        isMandatory: true,
        isWritable: true,
        isDeleteInChain: false,
        note: "",
        referral: [],
      },
      {
        id: 2,
        name: "optional-text",
        type: EntryAttributeTypeTypeEnum.TEXT,
        index: 1,
        isMandatory: false,
        isWritable: true,
        isDeleteInChain: false,
        note: "",
        referral: [],
      },
      {
        id: 3,
        name: "readonly-field",
        type: EntryAttributeTypeTypeEnum.STRING,
        index: 2,
        isMandatory: false,
        isWritable: false,
        isDeleteInChain: false,
        note: "",
        referral: [],
      },
    ],
    webhooks: [],
  };

  const entryInfo: Schema = {
    name: "test entry",
    schema: { id: 0, name: "testEntity" },
    attrs: {
      "1": {
        type: EntryAttributeTypeTypeEnum.STRING,
        index: 0,
        isMandatory: true,
        schema: {
          id: 1,
          name: "required-string",
        },
        value: {
          asString: "",
        },
      },
      "2": {
        type: EntryAttributeTypeTypeEnum.TEXT,
        index: 1,
        isMandatory: false,
        schema: {
          id: 2,
          name: "optional-text",
        },
        value: {
          asString: "",
        },
      },
      "3": {
        type: EntryAttributeTypeTypeEnum.STRING,
        index: 2,
        isMandatory: false,
        schema: {
          id: 3,
          name: "readonly-field",
        },
        value: {
          asString: "readonly value",
        },
      },
    },
  };

  test("should render a component with essential props", function () {
    const Wrapper: FC = () => {
      const { control, setValue } = useForm<Schema>({
        defaultValues: entryInfo,
      });
      return (
        <EntryForm entity={mockEntity} control={control} setValue={setValue} />
      );
    };

    expect(() =>
      render(<Wrapper />, {
        wrapper: TestWrapper,
      }),
    ).not.toThrow();
  });

  test("should display entry name field with value", () => {
    const Wrapper: FC = () => {
      const { control, setValue } = useForm<Schema>({
        defaultValues: entryInfo,
      });
      return (
        <EntryForm entity={mockEntity} control={control} setValue={setValue} />
      );
    };

    render(<Wrapper />, { wrapper: TestWrapper });

    const nameField = screen.getByDisplayValue("test entry");
    expect(nameField).toBeInTheDocument();
    expect(nameField).toHaveAttribute("id", "entry-name");
  });

  test("should display navigation chips for all fields", () => {
    const Wrapper: FC = () => {
      const { control, setValue } = useForm<Schema>({
        defaultValues: entryInfo,
      });
      return (
        <EntryForm entity={mockEntity} control={control} setValue={setValue} />
      );
    };

    render(<Wrapper />, { wrapper: TestWrapper });

    // Check navigation chips by their ID attributes
    expect(
      screen.getByRole("link", { name: /アイテム名/ }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /required-string/ }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /optional-text/ }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /readonly-field/ }),
    ).toBeInTheDocument();
  });

  test("should show required labels for mandatory fields", () => {
    const Wrapper: FC = () => {
      const { control, setValue } = useForm<Schema>({
        defaultValues: entryInfo,
      });
      return (
        <EntryForm entity={mockEntity} control={control} setValue={setValue} />
      );
    };

    render(<Wrapper />, { wrapper: TestWrapper });

    // Entry name is always required
    const nameRequiredLabel = screen.getAllByText("必須")[0];
    expect(nameRequiredLabel).toBeInTheDocument();

    // Required string field should show required label
    const requiredLabels = screen.getAllByText("必須");
    expect(requiredLabels).toHaveLength(2); // Name + required-string field
  });

  test("should disable readonly fields", () => {
    const Wrapper: FC = () => {
      const { control, setValue } = useForm<Schema>({
        defaultValues: entryInfo,
      });
      return (
        <EntryForm entity={mockEntity} control={control} setValue={setValue} />
      );
    };

    render(<Wrapper />, { wrapper: TestWrapper });

    // Check for permission denied text for readonly field
    expect(screen.getByText("Permission denied.")).toBeInTheDocument();
  });

  test("should update entry name on input change", async () => {
    const Wrapper: FC = () => {
      const { control, setValue, watch } = useForm<Schema>({
        resolver: zodResolver(schema),
        mode: "onBlur",
        defaultValues: entryInfo,
      });

      // Test helper to verify form state
      const nameValue = watch("name");
      React.useEffect(() => {
        if (nameValue === "updated entry name") {
          // Mark successful update for test verification
          document.body.setAttribute("data-name-updated", "true");
        }
      }, [nameValue]);

      return (
        <EntryForm entity={mockEntity} control={control} setValue={setValue} />
      );
    };

    render(<Wrapper />, { wrapper: TestWrapper });

    const nameField = screen.getByDisplayValue("test entry");

    await act(async () => {
      fireEvent.change(nameField, {
        target: { value: "updated entry name" },
      });
      fireEvent.blur(nameField);
    });

    await waitFor(() => {
      expect(nameField).toHaveValue("updated entry name");
    });

    // Verify form state was updated
    await waitFor(() => {
      expect(document.body).toHaveAttribute("data-name-updated", "true");
    });
  });

  test("should show scroll to top button and handle click", () => {
    const scrollToSpy = jest.fn();
    Object.defineProperty(window, "scrollTo", {
      value: scrollToSpy,
      writable: true,
    });

    const Wrapper: FC = () => {
      const { control, setValue } = useForm<Schema>({
        defaultValues: entryInfo,
      });
      return (
        <EntryForm entity={mockEntity} control={control} setValue={setValue} />
      );
    };

    render(<Wrapper />, { wrapper: TestWrapper });

    // Find button by ID since it may not have accessible name
    const scrollButton = document.getElementById("scroll_button");
    expect(scrollButton).toBeInTheDocument();

    fireEvent.click(scrollButton!);

    expect(scrollToSpy).toHaveBeenCalledWith({
      top: 0,
      behavior: "smooth",
    });
  });

  test("should validate required entry name field", async () => {
    const {
      result: {
        current: { control, setValue },
      },
    } = renderHook(() =>
      useForm<Schema>({
        resolver: zodResolver(schema),
        mode: "onBlur",
        defaultValues: {
          ...entryInfo,
          name: "", // Empty name should trigger validation error
        },
      }),
    );

    render(
      <EntryForm entity={mockEntity} control={control} setValue={setValue} />,
      { wrapper: TestWrapper },
    );

    // Get the specific entry name field by ID
    const nameField = document.getElementById("entry-name") as HTMLInputElement;
    expect(nameField).toBeInTheDocument();

    await act(async () => {
      fireEvent.blur(nameField);
    });

    // Wait for validation to complete
    await waitFor(() => {
      // Check if the field has validation error
      // Since the form starts with an empty name, it should be invalid
      expect(nameField.value).toBe("");
    });

    // Validation should mark the field as invalid when empty (required field)
    expect(nameField).toHaveAttribute("aria-invalid", "true");
  });

  test("should handle navigation chip clicks", () => {
    const Wrapper: FC = () => {
      const { control, setValue } = useForm<Schema>({
        defaultValues: entryInfo,
      });
      return (
        <EntryForm entity={mockEntity} control={control} setValue={setValue} />
      );
    };

    render(<Wrapper />, { wrapper: TestWrapper });

    // Find chips by ID instead of text to avoid duplicates
    const nameChip = document.getElementById("chip_name");
    expect(nameChip).toHaveAttribute("href", "#name");

    const stringFieldChip = document.getElementById("chip_required-string");
    expect(stringFieldChip).toHaveAttribute("href", "#attrs-required-string");
  });

  test("should render all attribute types correctly", () => {
    const entityWithAllTypes: EntityDetail = {
      ...mockEntity,
      attrs: [
        {
          id: 1,
          name: "string-field",
          type: EntryAttributeTypeTypeEnum.STRING,
          index: 0,
          isMandatory: false,
          isWritable: true,
          isDeleteInChain: false,
          note: "",
          referral: [],
        },
        {
          id: 2,
          name: "text-field",
          type: EntryAttributeTypeTypeEnum.TEXT,
          index: 1,
          isMandatory: false,
          isWritable: true,
          isDeleteInChain: false,
          note: "",
          referral: [],
        },
      ],
    };

    const attrsInfo: Schema = {
      name: "test entry",
      schema: { id: 0, name: "testEntity" },
      attrs: {
        "1": {
          type: EntryAttributeTypeTypeEnum.STRING,
          index: 0,
          isMandatory: false,
          schema: { id: 1, name: "string-field" },
          value: { asString: "" },
        },
        "2": {
          type: EntryAttributeTypeTypeEnum.TEXT,
          index: 1,
          isMandatory: false,
          schema: { id: 2, name: "text-field" },
          value: { asString: "" },
        },
      },
    };

    const Wrapper: FC = () => {
      const { control, setValue } = useForm<Schema>({
        defaultValues: attrsInfo,
      });
      return (
        <EntryForm
          entity={entityWithAllTypes}
          control={control}
          setValue={setValue}
        />
      );
    };

    render(<Wrapper />, { wrapper: TestWrapper });

    // Check for chips instead of table text to avoid duplicates
    expect(
      screen.getByRole("link", { name: /string-field/ }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /text-field/ }),
    ).toBeInTheDocument();
  });
});
