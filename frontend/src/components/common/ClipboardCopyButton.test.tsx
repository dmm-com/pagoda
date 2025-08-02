/**
 * @jest-environment jsdom
 */

import { fireEvent, render, screen } from "@testing-library/react";

import { ClipboardCopyButton } from "./ClipboardCopyButton";

import { TestWrapper } from "TestWrapper";

describe("ClipboardCopyButton", () => {
  test("renders button correctly", () => {
    render(<ClipboardCopyButton name="テスト名" />, { wrapper: TestWrapper });
    const button = screen.getByRole("button", { name: "名前をコピーする" });
    expect(button).toBeInTheDocument();
  });

  test("copies text to clipboard when clicked", async () => {
    // Mock clipboard API
    const writeTextMock = jest.fn();
    Object.defineProperty(navigator, "clipboard", {
      value: { writeText: writeTextMock },
      configurable: true,
    });

    render(<ClipboardCopyButton name="テスト名" />, { wrapper: TestWrapper });
    const button = screen.getByRole("button", { name: "名前をコピーする" });

    // ホバー時のTooltip
    fireEvent.mouseOver(button);
    expect(await screen.findByText("名前をコピーする")).toBeInTheDocument();

    // クリック
    fireEvent.click(button);
    expect(writeTextMock).toHaveBeenCalledWith("テスト名");

    // クリック後のTooltip
    fireEvent.mouseOver(button);
    expect(await screen.findByText("名前をコピーしました")).toBeInTheDocument();
  });
});
