import { act, fireEvent, render, screen, within } from "@testing-library/react";

import { TestWrapper } from "../../TestWrapper";

import { ExternalLinkConfirmDialog } from "./ExternalLinkConfirmDialog";

import i18n from "i18n/config";

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

  test("renders in English", async () => {
    await act(async () => {
      await i18n.changeLanguage("en");
    });

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
      within(dialog).getByText(
        "Are you sure you want to open the external site?",
      ),
    ).toBeInTheDocument();
  });
});
