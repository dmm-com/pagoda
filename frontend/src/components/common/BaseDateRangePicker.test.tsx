/**
 */

import { act, fireEvent, render, screen } from "@testing-library/react";

import { BaseDateRangePicker } from "./BaseDateRangePicker";

import { TestWrapper } from "TestWrapper";
import i18n from "i18n/config";

interface DatePickerProps {
  label: string;
  value: Date | null;
  onChange: (date: Date | null) => void;
  disabled?: boolean;
}

vi.mock("@mui/x-date-pickers", async () => ({
  ...(await vi.importActual("@mui/x-date-pickers")),
  DesktopDatePicker: ({
    label,
    value,
    onChange,
    disabled,
  }: DatePickerProps) => (
    <input
      aria-label={label}
      value={value ? value.toISOString().split("T")[0] : ""}
      onChange={(e) =>
        onChange(e.target.value ? new Date(e.target.value) : null)
      }
      disabled={disabled}
    />
  ),
  DateTimePicker: ({ label, value, onChange, disabled }: DatePickerProps) => (
    <input
      aria-label={label}
      value={value ? value.toISOString() : ""}
      onChange={(e) =>
        onChange(e.target.value ? new Date(e.target.value) : null)
      }
      disabled={disabled}
    />
  ),
}));

describe("BaseDateRangePicker", () => {
  const baseProps = {
    onApply: vi.fn(),
    onCancel: vi.fn(),
  };

  test("should show Japanese labels by default", () => {
    render(<BaseDateRangePicker {...baseProps} />, { wrapper: TestWrapper });

    expect(screen.getByLabelText("開始日")).toBeInTheDocument();
    expect(screen.getByLabelText("終了日")).toBeInTheDocument();
  });

  describe("English", () => {
    afterEach(async () => {
      await i18n.changeLanguage("ja");
    });

    test("should show English labels and buttons", async () => {
      await act(async () => {
        await i18n.changeLanguage("en");
      });

      render(<BaseDateRangePicker {...baseProps} />, { wrapper: TestWrapper });

      expect(screen.getByLabelText("Start date")).toBeInTheDocument();
      expect(screen.getByLabelText("End date")).toBeInTheDocument();

      fireEvent.change(screen.getByLabelText("Start date"), {
        target: { value: "2024-04-01" },
      });

      expect(
        await screen.findByRole("button", { name: "Cancel" }),
      ).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Apply" })).toBeInTheDocument();
    });
  });
});
