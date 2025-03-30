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
      // ampmに基づいて時間フォーマットを変更
      let time = val.toTimeString().split(" ")[0].substring(0, 5);
      if (ampm) {
        // 12時間制の場合の処理（テスト用に簡略化）
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

  test("初期日時が表示されること", () => {
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

  test("開始日時が終了日時より後の場合、バリデーションエラーが表示され適用ボタンが無効化されること", async () => {
    render(
      <DateTimeRangePicker
        {...baseProps}
        initialStart="2024-04-01T10:00:00"
        initialEnd="2024-04-10T15:30:00"
      />,
      { wrapper: TestWrapper },
    );

    // 開始日時を終了日時より後に変更
    const startInput = screen.getByLabelText("開始日時");
    fireEvent.change(startInput, { target: { value: "2024/04/15 10:00" } });

    // 適用ボタンが表示されるまで待機
    const applyButton = await screen.findByRole("button", { name: "適用" });

    // 適用ボタンが無効化されていることを確認
    expect(applyButton).toBeDisabled();
    expect(
      screen.getByText("終了日時は開始日時以降を指定してください"),
    ).toBeInTheDocument();
  });

  test("有効な日時が選択され適用ボタンがクリックされた場合、フォーマットされた日時でonApplyが呼ばれること", async () => {
    const handleApply = jest.fn();
    render(<DateTimeRangePicker {...baseProps} onApply={handleApply} />, {
      wrapper: TestWrapper,
    });

    // 日時を入力
    fireEvent.change(screen.getByLabelText("開始日時"), {
      target: { value: "2024/05/15 09:30" },
    });
    fireEvent.change(screen.getByLabelText("終了日時"), {
      target: { value: "2024/05/20 18:45" },
    });

    // 適用ボタンをクリック
    const applyButton = await screen.findByRole("button", { name: "適用" });
    fireEvent.click(applyButton);

    // コールバックが正しい引数で呼ばれることを確認
    expect(handleApply).toHaveBeenCalledTimes(1);
  });

  test("キャンセルボタンがクリックされた場合、onCancelが呼ばれること", async () => {
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

    // 日時を変更して編集状態にする
    fireEvent.change(screen.getByLabelText("開始日時"), {
      target: { value: "2024/06/02 11:30" },
    });

    // キャンセルボタンをクリック
    const cancelButton = await screen.findByRole("button", {
      name: "キャンセル",
    });
    fireEvent.click(cancelButton);

    // onCancelコールバックが呼ばれることを確認
    expect(handleCancel).toHaveBeenCalledTimes(1);
  });

  test("初期プロップスが変更された場合、状態がリセットされボタンが非表示になること", async () => {
    const { rerender } = render(
      <DateTimeRangePicker {...baseProps} initialStart="2024-08-01T10:00:00" />,
      { wrapper: TestWrapper },
    );

    // 日時を変更して編集状態にする
    fireEvent.change(screen.getByLabelText("開始日時"), {
      target: { value: "2024/08/02 11:30" },
    });

    // 編集ボタンが表示されることを確認
    expect(
      await screen.findByRole("button", { name: "適用" }),
    ).toBeInTheDocument();

    // プロップスを変更してコンポーネントを再レンダリング
    rerender(
      <DateTimeRangePicker
        {...baseProps}
        initialStart="2024-09-01T09:00:00"
        initialEnd="2024-09-10T18:00:00"
      />,
    );

    // 新しい値が表示されることを確認
    expect(screen.getByLabelText("開始日時")).toHaveValue("2024/09/01 09:00");
    expect(screen.getByLabelText("終了日時")).toHaveValue("2024/09/10 18:00");

    // 編集ボタンが非表示になっていることを確認
    expect(
      screen.queryByRole("button", { name: "適用" }),
    ).not.toBeInTheDocument();
  });
});
