/**
 * @jest-environment jsdom
 */

import { fireEvent, render, screen } from "@testing-library/react";

import { SubmitButton } from "./SubmitButton";

import { TestWrapper } from "TestWrapper";

// Mock MUI components
jest.mock("@mui/material", () => {
  const actual = jest.requireActual("@mui/material");
  return {
    ...actual,
    CircularProgress: ({ size }: { size: string }) => (
      <div data-testid="circular-progress" data-size={size}></div>
    ),
  };
});

describe("SubmitButton", () => {
  // Basic rendering test
  test("renders submit button correctly", () => {
    const handleSubmit = jest.fn();

    render(
      <SubmitButton
        name="送信"
        disabled={false}
        isSubmitting={false}
        handleSubmit={handleSubmit}
      />,
      { wrapper: TestWrapper },
    );

    const submitButton = screen.getByText("送信");
    expect(submitButton).toBeInTheDocument();
    expect(submitButton.closest("button")).not.toBeDisabled();

    // Cancel button should not be displayed
    expect(screen.queryByText("キャンセル")).not.toBeInTheDocument();
  });

  // Test disabled state
  test("disables button when disabled prop is true", () => {
    const handleSubmit = jest.fn();

    render(
      <SubmitButton
        name="送信"
        disabled={true}
        isSubmitting={false}
        handleSubmit={handleSubmit}
      />,
      { wrapper: TestWrapper },
    );

    const submitButton = screen.getByText("送信");
    expect(submitButton.closest("button")).toBeDisabled();
  });

  // Test isSubmitting state
  test("shows loading indicator when isSubmitting is true", () => {
    const handleSubmit = jest.fn();

    render(
      <SubmitButton
        name="送信"
        disabled={false}
        isSubmitting={true}
        handleSubmit={handleSubmit}
      />,
      { wrapper: TestWrapper },
    );

    expect(screen.getByTestId("circular-progress")).toBeInTheDocument();
    expect(screen.getByTestId("circular-progress")).toHaveAttribute(
      "data-size",
      "20px",
    );
  });

  // Test handleSubmit callback
  test("calls handleSubmit when button is clicked", () => {
    const handleSubmit = jest.fn();

    render(
      <SubmitButton
        name="送信"
        disabled={false}
        isSubmitting={false}
        handleSubmit={handleSubmit}
      />,
      { wrapper: TestWrapper },
    );

    const submitButton = screen.getByText("送信").closest("button");
    if (submitButton) {
      fireEvent.click(submitButton);
      expect(handleSubmit).toHaveBeenCalledTimes(1);
    }
  });

  // Test handleCancel
  test("renders cancel button when handleCancel is provided", () => {
    const handleSubmit = jest.fn();
    const handleCancel = jest.fn();

    render(
      <SubmitButton
        name="送信"
        disabled={false}
        isSubmitting={false}
        handleSubmit={handleSubmit}
        handleCancel={handleCancel}
      />,
      { wrapper: TestWrapper },
    );

    const cancelButton = screen.getByText("キャンセル");
    expect(cancelButton).toBeInTheDocument();
  });

  // Test cancel button click
  test("calls handleCancel when cancel button is clicked", () => {
    const handleSubmit = jest.fn();
    const handleCancel = jest.fn();

    render(
      <SubmitButton
        name="送信"
        disabled={false}
        isSubmitting={false}
        handleSubmit={handleSubmit}
        handleCancel={handleCancel}
      />,
      { wrapper: TestWrapper },
    );

    const cancelButton = screen.getByText("キャンセル").closest("button");
    if (cancelButton) {
      fireEvent.click(cancelButton);
      expect(handleCancel).toHaveBeenCalledTimes(1);
    }
  });
});
