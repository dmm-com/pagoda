/**
 * @jest-environment jsdom
 */

import { fireEvent, render, screen } from "@testing-library/react";
import React from "react";

import { TestWrapper } from "TestWrapper";
import { DateTimeRangePicker } from "components/common/DateTimeRangePicker";

interface DateTimePickerProps {
  label: string;
  value: Date | null;
  onChange: (date: Date | null) => void;
  disabled?: boolean;
  ampm?: boolean;
  slotProps?: {
    textField?: Record<string, unknown>;
  };
}

jest.mock("@mui/x-date-pickers", () => ({
  ...jest.requireActual("@mui/x-date-pickers"),
  DateTimePicker: ({
    label,
    value,
    onChange,
    disabled,
    ampm = false,
    slotProps,
  }: DateTimePickerProps) => {
    const formatValue = (val: Date | null) => {
      if (!val) return "";
      const date = val.toISOString().split("T")[0].replace(/-/g, "/");
      // Change time format based on ampm setting
      let time = val.toTimeString().split(" ")[0].substring(0, 5);
      if (ampm) {
        // Processing for 12-hour format (simplified for testing)
        const hours = parseInt(time.split(":")[0], 10);
        const minutes = time.split(":")[1];
        const period = hours >= 12 ? "PM" : "AM";
        const hour12 = hours % 12 || 12;
        time = `${hour12}:${minutes} ${period}`;
      }
      return `${date} ${time}`;
    };

    return (
      <div>
        <label>{label}</label>
        <input
          type="text"
          data-testid={`datetimepicker-${label}`}
          value={formatValue(value)}
          onChange={(e) => {
            const [dateStr, timeStr] = e.target.value.split(" ");
            const dateValue = dateStr
              ? new Date(`${dateStr.replace(/\//g, "-")}T${timeStr || "00:00"}`)
              : null;
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

describe("DateTimeRangePicker", () => {
  const baseProps = {
    onApply: jest.fn(),
    onCancel: jest.fn(),
    disabled: false,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("Initial date and time should be displayed correctly", () => {
    render(
      <DateTimeRangePicker
        {...baseProps}
        initialStart="2024-04-01T10:00:00"
        initialEnd="2024-04-10T15:30:00"
      />,
      { wrapper: TestWrapper },
    );

    expect(screen.getByLabelText("開始日時")).toHaveValue("2024/04/01 10:00");
    expect(screen.getByLabelText("終了日時")).toHaveValue("2024/04/10 15:30");
    expect(
      screen.queryByRole("button", { name: "適用" }),
    ).not.toBeInTheDocument();
  });

  test("When start date is after end date, validation error should be displayed and apply button should be disabled", async () => {
    render(
      <DateTimeRangePicker
        {...baseProps}
        initialStart="2024-04-01T10:00:00"
        initialEnd="2024-04-10T15:30:00"
      />,
      { wrapper: TestWrapper },
    );

    // Change start date to be after end date
    const startInput = screen.getByLabelText("開始日時");
    fireEvent.change(startInput, { target: { value: "2024/04/15 10:00" } });

    // Wait for apply button to appear
    const applyButton = await screen.findByRole("button", { name: "適用" });

    // Confirm apply button is disabled
    expect(applyButton).toBeDisabled();
    expect(
      screen.getByText("終了日時は開始日時以降を指定してください"),
    ).toBeInTheDocument();
  });

  test("When valid dates are selected and apply button is clicked, onApply should be called with formatted dates", async () => {
    const handleApply = jest.fn();
    render(<DateTimeRangePicker {...baseProps} onApply={handleApply} />, {
      wrapper: TestWrapper,
    });

    // Input dates
    fireEvent.change(screen.getByLabelText("開始日時"), {
      target: { value: "2024/05/15 09:30" },
    });
    fireEvent.change(screen.getByLabelText("終了日時"), {
      target: { value: "2024/05/20 18:45" },
    });

    // Click apply button
    const applyButton = await screen.findByRole("button", { name: "適用" });
    fireEvent.click(applyButton);

    // Verify callback is called with correct arguments
    expect(handleApply).toHaveBeenCalledTimes(1);

    // Verify ISO8601 formatted date strings are passed
    // Note: Due to mock Date object behavior, exact dates may vary by environment, so we verify the pattern with regex
    expect(handleApply).toHaveBeenCalledWith(
      expect.stringMatching(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/),
      expect.stringMatching(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/),
    );
  });

  test("When cancel button is clicked, onCancel should be called", async () => {
    const handleCancel = jest.fn();
    render(
      <DateTimeRangePicker
        {...baseProps}
        onCancel={handleCancel}
        initialStart="2024-06-01T10:00:00"
        initialEnd="2024-06-05T15:00:00"
      />,
      { wrapper: TestWrapper },
    );

    // Change date to enter edit mode
    fireEvent.change(screen.getByLabelText("開始日時"), {
      target: { value: "2024/06/02 11:30" },
    });

    // Click cancel button
    const cancelButton = await screen.findByRole("button", {
      name: "キャンセル",
    });
    fireEvent.click(cancelButton);

    // Verify onCancel callback is called
    expect(handleCancel).toHaveBeenCalledTimes(1);
  });

  test("When initial props change, state should reset and buttons should be hidden", async () => {
    const { rerender } = render(
      <DateTimeRangePicker {...baseProps} initialStart="2024-08-01T10:00:00" />,
      { wrapper: TestWrapper },
    );

    // Change date to enter edit mode
    fireEvent.change(screen.getByLabelText("開始日時"), {
      target: { value: "2024/08/02 11:30" },
    });

    // Verify edit buttons are displayed
    expect(
      await screen.findByRole("button", { name: "適用" }),
    ).toBeInTheDocument();

    // Change props and rerender component
    rerender(
      <DateTimeRangePicker
        {...baseProps}
        initialStart="2024-09-01T09:00:00"
        initialEnd="2024-09-10T18:00:00"
      />,
    );

    // Verify new values are displayed
    expect(screen.getByLabelText("開始日時")).toHaveValue("2024/09/01 09:00");
    expect(screen.getByLabelText("終了日時")).toHaveValue("2024/09/10 18:00");

    // Verify edit buttons are hidden
    expect(
      screen.queryByRole("button", { name: "適用" }),
    ).not.toBeInTheDocument();
  });
});
