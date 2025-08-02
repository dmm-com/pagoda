/**
 * @jest-environment jsdom
 */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import { TestWrapper } from "TestWrapper";
import { DateRangePicker } from "components/common/DateRangePicker";

interface DesktopDatePickerProps {
  label: string;
  value: Date | null;
  onChange: (date: Date | null) => void;
  disabled?: boolean;
  slotProps?: {
    textField?: Record<string, unknown>;
  };
}

jest.mock("@mui/x-date-pickers", () => ({
  ...jest.requireActual("@mui/x-date-pickers"),
  DesktopDatePicker: ({
    label,
    value,
    onChange,
    disabled,
    slotProps,
  }: DesktopDatePickerProps) => {
    const formatValue = (val: Date | null) => {
      if (!val) return "";
      return val.toISOString().split("T")[0].replace(/-/g, "/");
    };

    return (
      <div>
        <label>{label}</label>
        <input
          type="text"
          data-testid={`datepicker-${label}`}
          value={formatValue(value)}
          onChange={(e) => {
            const dateStr = e.target.value.replace(/\//g, "-");
            const dateValue = dateStr ? new Date(dateStr) : null;
            onChange(dateValue);
          }}
          disabled={disabled}
          aria-label={label}
          {...(slotProps?.textField ?? {})}
        />
      </div>
    );
  },
}));

describe("DateRangePicker", () => {
  const baseProps = {
    onApply: jest.fn(),
    onCancel: jest.fn(),
    disabled: false,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("should display initial dates when provided", () => {
    render(
      <DateRangePicker
        {...baseProps}
        initialStart="2024-04-01"
        initialEnd="2024-04-10"
      />,
      { wrapper: TestWrapper },
    );

    expect(screen.getByLabelText("開始日")).toHaveValue("2024/04/01");
    expect(screen.getByLabelText("終了日")).toHaveValue("2024/04/10");
    expect(
      screen.queryByRole("button", { name: "適用" }),
    ).not.toBeInTheDocument();
  });

  test("should show validation error and disable apply when start date is after end date", async () => {
    render(
      <DateRangePicker
        {...baseProps}
        initialStart="2024-04-01"
        initialEnd="2024-04-10"
      />,
      { wrapper: TestWrapper },
    );

    // Change start date to after end date
    const startInput = screen.getByLabelText("開始日");
    fireEvent.change(startInput, { target: { value: "2024/04/15" } });

    // Wait until the apply button appears
    const applyButton = await screen.findByRole("button", { name: "適用" });

    // The apply button should be disabled
    expect(applyButton).toBeDisabled();
  });

  test("should call onApply with formatted dates when valid dates are selected and apply is clicked", async () => {
    const handleApply = jest.fn();
    render(<DateRangePicker {...baseProps} onApply={handleApply} />, {
      wrapper: TestWrapper,
    });

    // Input dates
    fireEvent.change(screen.getByLabelText("開始日"), {
      target: { value: "2024/05/15" },
    });
    fireEvent.change(screen.getByLabelText("終了日"), {
      target: { value: "2024/05/20" },
    });

    // Click the apply button
    const applyButton = await screen.findByRole("button", { name: "適用" });
    fireEvent.click(applyButton);

    // The callback should be called with the correct arguments
    expect(handleApply).toHaveBeenCalledWith("2024-05-15", "2024-05-20");
  });

  test("should call onCancel when cancel button is clicked", async () => {
    const handleCancel = jest.fn();
    render(
      <DateRangePicker
        {...baseProps}
        onCancel={handleCancel}
        initialStart="2024-06-01"
        initialEnd="2024-06-05"
      />,
      { wrapper: TestWrapper },
    );

    // Change the date to edit
    fireEvent.change(screen.getByLabelText("開始日"), {
      target: { value: "2024/06/02" },
    });

    // Click the cancel button
    const cancelButton = await screen.findByRole("button", {
      name: "キャンセル",
    });
    fireEvent.click(cancelButton);

    // The onCancel callback should be called
    expect(handleCancel).toHaveBeenCalledTimes(1);

    // The buttons should still be visible
    expect(
      screen.getByRole("button", { name: "キャンセル" }),
    ).toBeInTheDocument();
  });

  test("should disable inputs when disabled prop is true", () => {
    render(<DateRangePicker {...baseProps} disabled={true} />, {
      wrapper: TestWrapper,
    });

    // The input fields should be disabled
    expect(screen.getByLabelText("開始日")).toBeDisabled();
    expect(screen.getByLabelText("終了日")).toBeDisabled();
  });

  test("should not show action buttons when not editing initially", () => {
    render(<DateRangePicker {...baseProps} />, { wrapper: TestWrapper });

    // The buttons should not be displayed in the initial state
    expect(
      screen.queryByRole("button", { name: "適用" }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "キャンセル" }),
    ).not.toBeInTheDocument();
  });

  test("should show action buttons after editing", async () => {
    render(<DateRangePicker {...baseProps} />, { wrapper: TestWrapper });

    // Change the date
    fireEvent.change(screen.getByLabelText("開始日"), {
      target: { value: "2024/07/01" },
    });

    // Wait until the buttons are displayed
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "適用" })).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: "キャンセル" }),
      ).toBeInTheDocument();
    });
  });

  test("should reset state and hide buttons when initial props change", async () => {
    const { rerender } = render(
      <DateRangePicker {...baseProps} initialStart="2024-08-01" />,
      { wrapper: TestWrapper },
    );

    // Change the date to edit
    fireEvent.change(screen.getByLabelText("開始日"), {
      target: { value: "2024/08/02" },
    });

    // Wait until the buttons are displayed
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "適用" })).toBeInTheDocument();
    });

    // Rerender with different initial values
    rerender(
      <DateRangePicker
        {...baseProps}
        initialStart="2024-09-01"
        initialEnd="2024-09-10"
      />,
    );

    // The dates should be updated
    expect(screen.getByLabelText("開始日")).toHaveValue("2024/09/01");
    expect(screen.getByLabelText("終了日")).toHaveValue("2024/09/10");

    // The buttons should be hidden
    expect(
      screen.queryByRole("button", { name: "適用" }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "キャンセル" }),
    ).not.toBeInTheDocument();
  });
});
