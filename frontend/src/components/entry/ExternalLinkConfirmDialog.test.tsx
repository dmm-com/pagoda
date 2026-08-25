import { fireEvent, render, screen, within } from "@testing-library/react";

import { TestWrapper } from "../../TestWrapper";

import { ExternalLinkConfirmDialog } from "./ExternalLinkConfirmDialog";

describe("ExternalLinkConfirmDialog", () => {
  test("opens a confirmation dialog before navigating to an external url", () => {
    const openSpy = vi.spyOn(window, "open").mockImplementation(() => null);

    render(
      <ExternalLinkConfirmDialog url="https://example.com/docs">
        https://example.com/docs
      </ExternalLinkConfirmDialog>,
      { wrapper: TestWrapper },
    );

    fireEvent.click(
      screen.getByRole("button", { name: "https://example.com/docs" }),
    );

    const dialog = screen.getByRole("dialog");
    expect(
      within(dialog).getByText("外部サイトを開きますか？"),
    ).toBeInTheDocument();
    expect(
      within(dialog).getByText("https://example.com/docs"),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Open" }));

    expect(openSpy).toHaveBeenCalledWith(
      "https://example.com/docs",
      "_blank",
      "noopener,noreferrer",
    );

    openSpy.mockRestore();
  });
});
