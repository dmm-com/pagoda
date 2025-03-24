/**
 * @jest-environment jsdom
 */

import { fireEvent, render, screen } from "@testing-library/react";
import React from "react";

import { ClipboardCopyButton } from "./ClipboardCopyButton";

import { TestWrapper } from "TestWrapper";

// Mock MUI Tooltip component
jest.mock("@mui/material", () => {
  const actual = jest.requireActual("@mui/material");
  return {
    ...actual,
    Tooltip: ({
      children,
      title,
    }: {
      children: React.ReactNode;
      title: string;
    }) => (
      <div data-testid="tooltip" data-title={title}>
        {children}
      </div>
    ),
    ClickAwayListener: ({
      children,
      onClickAway,
    }: {
      children: React.ReactNode;
      onClickAway: () => void;
    }) => (
      <div data-testid="click-away-listener" onClick={onClickAway}>
        {children}
      </div>
    ),
  };
});

describe("ClipboardCopyButton", () => {
  test("renders button correctly", () => {
    render(<ClipboardCopyButton name="テスト名" />, { wrapper: TestWrapper });

    // Verify button exists
    const button = screen.getByRole("button");
    expect(button).toBeInTheDocument();

    // Verify tooltip is correctly configured
    const tooltips = screen.getAllByTestId("tooltip");
    expect(
      tooltips.some((t) => t.dataset.title === "名前をコピーする"),
    ).toBeTruthy();
  });

  test("copies text to clipboard when clicked", () => {
    // Mock clipboard API
    const writeTextMock = jest.fn();
    Object.defineProperty(navigator, "clipboard", {
      value: { writeText: writeTextMock },
      configurable: true,
    });

    render(<ClipboardCopyButton name="テスト名" />, { wrapper: TestWrapper });

    // Click the button
    const button = screen.getByRole("button");
    fireEvent.click(button);

    // Verify clipboard API was called
    expect(writeTextMock).toHaveBeenCalledWith("テスト名");

    // Verify copy completion tooltip is set
    const tooltips = screen.getAllByTestId("tooltip");
    expect(
      tooltips.some((t) => t.dataset.title === "名前をコピーしました"),
    ).toBeTruthy();
  });

  test("renders ClickAwayListener correctly", () => {
    render(<ClipboardCopyButton name="テスト名" />, { wrapper: TestWrapper });

    // Verify ClickAwayListener exists
    const clickAwayListener = screen.getByTestId("click-away-listener");
    expect(clickAwayListener).toBeInTheDocument();

    // Simulate click event
    fireEvent.click(clickAwayListener);

    // Verify it executes without crashing (implicit assertion)
  });
});
