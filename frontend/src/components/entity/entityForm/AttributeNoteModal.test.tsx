/**
 * @jest-environment jsdom
 */
import { render, screen, fireEvent } from "@testing-library/react";
import React from "react";
import { useForm } from "react-hook-form";

import { AttributeNoteModal } from "./AttributeNoteModal";
import { Schema } from "./EntityFormSchema";

import { TestWrapper } from "TestWrapper";

const TestModal = ({
  initialNote = "",
  idx = 0,
  onClose = jest.fn(),
  onForm,
}: {
  initialNote?: string;
  idx?: number;
  onClose?: () => void;
  onForm?: (form: ReturnType<typeof useForm<Schema>>) => void;
}) => {
  const form = useForm<Schema>({
    defaultValues: { attrs: [{ note: initialNote }] },
  });
  onForm?.(form);
  return (
    <AttributeNoteModal
      index={idx}
      control={form.control}
      handleCloseModal={onClose}
    />
  );
};

describe("AttributeNoteModal", () => {
  test("should reflect initial value in TextField", () => {
    render(<TestModal initialNote="既存メモ" />, { wrapper: TestWrapper });
    const input = screen.getByPlaceholderText("説明") as HTMLInputElement;
    expect(input.value).toBe("既存メモ");
  });

  test("should update value in form.getValues() after input change", () => {
    let form: ReturnType<typeof useForm<Schema>> | undefined;
    render(
      <TestModal
        initialNote="初期メモ"
        onForm={(f) => {
          form = f;
        }}
      />,
      { wrapper: TestWrapper },
    );
    const input = screen.getByPlaceholderText("説明");
    fireEvent.change(input, { target: { value: "更新済みメモ" } });
    expect(form!.getValues().attrs[0].note).toBe("更新済みメモ");
  });

  test("should render TextField and title when index >= 0 (modal open)", () => {
    render(<TestModal />, { wrapper: TestWrapper });
    expect(screen.getByPlaceholderText("説明")).toBeInTheDocument();
    expect(screen.getByText("属性説明")).toBeInTheDocument();
  });

  test("should call handleCloseModal when clicking close button", () => {
    const onClose = jest.fn();
    render(<TestModal onClose={onClose} />, { wrapper: TestWrapper });
    const input = screen.getByPlaceholderText("説明");
    fireEvent.change(input, { target: { value: "テストメモ" } });
    fireEvent.click(screen.getByText("閉じる"));
    expect(onClose).toHaveBeenCalled();
  });

  test("should not render modal when index < 0", () => {
    render(<TestModal idx={-1} />, { wrapper: TestWrapper });
    expect(screen.queryByRole("dialog")).toBeNull();
  });
});
