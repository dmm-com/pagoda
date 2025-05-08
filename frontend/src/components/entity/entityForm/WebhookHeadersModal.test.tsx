/**
 * @jest-environment jsdom
 */
import { render, screen, fireEvent } from "@testing-library/react";
import React from "react";
import { useForm } from "react-hook-form";

import { Schema } from "./EntityFormSchema";
import { WebhookHeadersModal } from "./WebhookHeadersModal";

import { TestWrapper } from "TestWrapper";

type WebhookHeader = { headerKey: string; headerValue: string };

const TestModal = ({
  initialHeaders = [],
  idx = 0,
  onClose = jest.fn(),
  onForm,
}: {
  initialHeaders?: WebhookHeader[];
  idx?: number;
  onClose?: () => void;
  onForm?: (form: ReturnType<typeof useForm<Schema>>) => void;
}) => {
  const form = useForm<Schema>({
    defaultValues: { webhooks: [{ headers: initialHeaders }] },
  });
  onForm?.(form);
  return (
    <WebhookHeadersModal
      webhookIndex={idx}
      control={form.control}
      handleCloseModal={onClose}
    />
  );
};

describe("WebhookHeadersModal", () => {
  test("should reflect initial headers in TextFields", () => {
    const headers = [
      { headerKey: "X-Test-Key", headerValue: "value1" },
      { headerKey: "X-Another", headerValue: "value2" },
    ];
    render(<TestModal initialHeaders={headers} />, { wrapper: TestWrapper });
    expect(screen.getByDisplayValue("X-Test-Key")).toBeInTheDocument();
    expect(screen.getByDisplayValue("value1")).toBeInTheDocument();
    expect(screen.getByDisplayValue("X-Another")).toBeInTheDocument();
    expect(screen.getByDisplayValue("value2")).toBeInTheDocument();
  });

  test("should update value in form.getValues() after input change", () => {
    let form: ReturnType<typeof useForm<Schema>> | undefined;
    const headers = [{ headerKey: "X-Init", headerValue: "init" }];
    render(
      <TestModal
        initialHeaders={headers}
        onForm={(f) => {
          form = f;
        }}
      />,
      { wrapper: TestWrapper },
    );
    const keyInput = screen.getByDisplayValue("X-Init");
    fireEvent.change(keyInput, { target: { value: "X-Updated" } });
    const valueInput = screen.getByDisplayValue("init");
    fireEvent.change(valueInput, { target: { value: "updated-value" } });
    expect(form!.getValues().webhooks[0].headers[0].headerKey).toBe(
      "X-Updated",
    );
    expect(form!.getValues().webhooks[0].headers[0].headerValue).toBe(
      "updated-value",
    );
  });

  test("should add header row when clicking add button", () => {
    render(<TestModal initialHeaders={[]} />, { wrapper: TestWrapper });
    expect(
      (screen.getAllByLabelText("Key")[0] as HTMLInputElement).disabled,
    ).toBe(true);

    const addBtns = screen
      .getAllByRole("button")
      .filter((btn) => btn.querySelector("svg"));
    fireEvent.click(addBtns[addBtns.length - 1]);
    expect(
      screen
        .getAllByLabelText("Key")
        .some((input) => !(input as HTMLInputElement).disabled),
    ).toBe(true);
  });

  test("should delete header row when clicking delete button", () => {
    const headers = [{ headerKey: "X-Del", headerValue: "to-delete" }];
    render(<TestModal initialHeaders={headers} />, { wrapper: TestWrapper });

    const delBtns = screen
      .getAllByRole("button")
      .filter((btn) =>
        btn.querySelector('svg[data-testid="DeleteOutlineIcon"]'),
      );
    fireEvent.click(delBtns[0]);
    expect(screen.queryByDisplayValue("X-Del")).toBeNull();
    expect(screen.queryByDisplayValue("to-delete")).toBeNull();
  });

  test("should call handleCloseModal when clicking close button", () => {
    const onClose = jest.fn();
    render(<TestModal onClose={onClose} />, { wrapper: TestWrapper });
    fireEvent.click(screen.getByText("閉じる"));
    expect(onClose).toHaveBeenCalled();
  });

  test("should not render modal when idx < 0", () => {
    render(<TestModal idx={-1} />, { wrapper: TestWrapper });
    expect(screen.queryByRole("dialog")).toBeNull();
  });
});
