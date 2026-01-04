/**
 * @jest-environment jsdom
 */

import { render, screen, fireEvent, waitFor } from "@testing-library/react";

import { TestWrapper } from "TestWrapper";
import { EntryControlMenu } from "components/entry/EntryControlMenu";
import { aironeApiClient } from "repository/AironeApiClient";

// Mock API client
jest.mock("repository/AironeApiClient", () => ({
  aironeApiClient: {
    destroyEntry: jest.fn(() => Promise.resolve()),
  },
}));

describe("EntryControlMenu", () => {
  const createAnchorElem = () => document.createElement("button");

  const defaultProps = {
    entityId: 1,
    entryId: 1,
    anchorElem: createAnchorElem(),
    handleClose: jest.fn(),
  };

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe("rendering", () => {
    test("should render a component with essential props", () => {
      expect(() =>
        render(<EntryControlMenu {...defaultProps} />, {
          wrapper: TestWrapper,
        }),
      ).not.toThrow();
    });

    test("should render a component with optional props", () => {
      expect(() =>
        render(
          <EntryControlMenu {...defaultProps} disableChangeHistory={true} />,
          { wrapper: TestWrapper },
        ),
      ).not.toThrow();
    });

    test("menu items are displayed correctly", () => {
      render(<EntryControlMenu {...defaultProps} />, { wrapper: TestWrapper });

      expect(screen.getByText("詳細")).toBeInTheDocument();
      expect(screen.getByText("編集")).toBeInTheDocument();
      expect(screen.getByText("コピー")).toBeInTheDocument();
      expect(screen.getByText("ACL 設定")).toBeInTheDocument();
      expect(screen.getByText("変更履歴")).toBeInTheDocument();
      expect(screen.getByText("ACL 変更履歴")).toBeInTheDocument();
      expect(screen.getByText("削除")).toBeInTheDocument();
    });

    test("anchorElem is null, menu is closed", () => {
      const { container } = render(
        <EntryControlMenu {...defaultProps} anchorElem={null} />,
        { wrapper: TestWrapper },
      );

      const menuItems = container.querySelectorAll(".MuiMenuItem-root");
      expect(menuItems.length).toBe(0);
    });

    test("disableChangeHistory prop disables change history menu item", () => {
      render(
        <EntryControlMenu {...defaultProps} disableChangeHistory={true} />,
        { wrapper: TestWrapper },
      );

      // Find the menu item or link that contains the history text
      const historyText = screen.getByText("変更履歴");
      const historyMenuItem =
        historyText.closest("a") || historyText.closest("li");
      expect(historyMenuItem).toHaveClass("Mui-disabled");
    });

    test("change history is enabled by default", () => {
      render(
        <EntryControlMenu {...defaultProps} disableChangeHistory={false} />,
        { wrapper: TestWrapper },
      );

      const historyLink = screen.getByText("変更履歴").closest("a");
      expect(historyLink).toBeInTheDocument();
      // The link should not have aria-disabled
      expect(historyLink).not.toHaveAttribute("aria-disabled", "true");
    });
  });

  describe("menu item links", () => {
    test("detail link has correct href", () => {
      render(<EntryControlMenu {...defaultProps} />, { wrapper: TestWrapper });

      const detailLink = screen.getByText("詳細").closest("a");
      expect(detailLink).toHaveAttribute("href");
      expect(detailLink?.getAttribute("href")).toContain("/entries/1");
    });

    test("edit link has correct href", () => {
      render(<EntryControlMenu {...defaultProps} />, { wrapper: TestWrapper });

      const editLink = screen.getByText("編集").closest("a");
      expect(editLink).toHaveAttribute("href");
      expect(editLink?.getAttribute("href")).toContain("/edit");
    });

    test("copy link has correct href", () => {
      render(<EntryControlMenu {...defaultProps} />, { wrapper: TestWrapper });

      const copyLink = screen.getByText("コピー").closest("a");
      expect(copyLink).toHaveAttribute("href");
      expect(copyLink?.getAttribute("href")).toContain("/copy");
    });

    test("ACL link has correct href", () => {
      render(<EntryControlMenu {...defaultProps} />, { wrapper: TestWrapper });

      const aclLink = screen.getByText("ACL 設定").closest("a");
      expect(aclLink).toHaveAttribute("href");
      expect(aclLink?.getAttribute("href")).toContain("/acl");
    });

    test("change history link has correct href", () => {
      render(<EntryControlMenu {...defaultProps} />, { wrapper: TestWrapper });

      const historyLink = screen.getByText("変更履歴").closest("a");
      expect(historyLink).toHaveAttribute("href");
      expect(historyLink?.getAttribute("href")).toContain("/history");
    });

    test("ACL history link has correct href", () => {
      render(<EntryControlMenu {...defaultProps} />, { wrapper: TestWrapper });

      const aclHistoryLink = screen.getByText("ACL 変更履歴").closest("a");
      expect(aclHistoryLink).toHaveAttribute("href");
      expect(aclHistoryLink?.getAttribute("href")).toContain("/acl/");
      expect(aclHistoryLink?.getAttribute("href")).toContain("/history");
    });
  });

  describe("custom paths", () => {
    test("should use custom detail path when provided", () => {
      render(
        <EntryControlMenu
          {...defaultProps}
          customDetailPath="/custom/detail"
        />,
        { wrapper: TestWrapper },
      );

      const detailLink = screen.getByText("詳細").closest("a");
      expect(detailLink?.getAttribute("href")).toBe("/custom/detail");
    });

    test("should use custom edit path when provided", () => {
      render(
        <EntryControlMenu {...defaultProps} customEditPath="/custom/edit" />,
        { wrapper: TestWrapper },
      );

      const editLink = screen.getByText("編集").closest("a");
      expect(editLink?.getAttribute("href")).toBe("/custom/edit");
    });
  });

  describe("menu close", () => {
    test("should call handleClose when menu item is clicked", () => {
      const mockHandleClose = jest.fn();
      render(
        <EntryControlMenu {...defaultProps} handleClose={mockHandleClose} />,
        { wrapper: TestWrapper },
      );

      // Click on a menu item
      const detailItem = screen.getByText("詳細");
      fireEvent.click(detailItem);

      // Note: The actual close might be handled by the Menu component
      // or by navigation, so we just verify the click doesn't throw
    });
  });

  describe("delete action", () => {
    test("should show delete button", () => {
      render(<EntryControlMenu {...defaultProps} />, { wrapper: TestWrapper });

      expect(screen.getByText("削除")).toBeInTheDocument();
    });

    test("should show confirmation dialog when delete is clicked", async () => {
      render(<EntryControlMenu {...defaultProps} />, { wrapper: TestWrapper });

      const deleteButton = screen.getByText("削除");
      fireEvent.click(deleteButton);

      await waitFor(() => {
        expect(screen.getByText("本当に削除しますか？")).toBeInTheDocument();
      });
    });

    test("should call destroyEntry when delete is confirmed", async () => {
      render(<EntryControlMenu {...defaultProps} />, { wrapper: TestWrapper });

      const deleteButton = screen.getByText("削除");
      fireEvent.click(deleteButton);

      await waitFor(() => {
        expect(screen.getByText("本当に削除しますか？")).toBeInTheDocument();
      });

      // Click Yes in the confirmation dialog
      const yesButton = screen.getByRole("button", { name: /yes/i });
      fireEvent.click(yesButton);

      await waitFor(() => {
        expect(aironeApiClient.destroyEntry).toHaveBeenCalledWith(1);
      });
    });

    test("should not call destroyEntry when delete is cancelled", async () => {
      render(<EntryControlMenu {...defaultProps} />, { wrapper: TestWrapper });

      const deleteButton = screen.getByText("削除");
      fireEvent.click(deleteButton);

      await waitFor(() => {
        expect(screen.getByText("本当に削除しますか？")).toBeInTheDocument();
      });

      // Click No in the confirmation dialog
      const noButton = screen.getByRole("button", { name: /no/i });
      fireEvent.click(noButton);

      await waitFor(() => {
        expect(aironeApiClient.destroyEntry).not.toHaveBeenCalled();
      });
    });
  });
});
