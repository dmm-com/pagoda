/**
 * @jest-environment jsdom
 */

import { render, screen, fireEvent } from "@testing-library/react";

import { EntityImportModal } from "./EntityImportModal";

import { TestWrapper } from "TestWrapper";

// Mock API client
jest.mock("../../repository/AironeApiClient", () => ({
  aironeApiClient: {
    importEntities: jest.fn(() => Promise.resolve()),
  },
}));

describe("EntityImportModal", () => {
  const defaultProps = {
    openImportModal: true,
    closeImportModal: jest.fn(),
  };

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe("rendering", () => {
    test("should render modal when open", () => {
      render(<EntityImportModal {...defaultProps} />, { wrapper: TestWrapper });

      expect(screen.getByText("モデルのインポート")).toBeInTheDocument();
    });

    test("should render description text", () => {
      render(<EntityImportModal {...defaultProps} />, { wrapper: TestWrapper });

      expect(
        screen.getByText("インポートするファイルを選択してください。"),
      ).toBeInTheDocument();
    });

    test("should render caption about CSV files", () => {
      render(<EntityImportModal {...defaultProps} />, { wrapper: TestWrapper });

      expect(
        screen.getByText("※CSV形式のファイルは選択できません。"),
      ).toBeInTheDocument();
    });

    test("should not render modal content when closed", () => {
      render(<EntityImportModal {...defaultProps} openImportModal={false} />, {
        wrapper: TestWrapper,
      });

      expect(screen.queryByText("モデルのインポート")).not.toBeInTheDocument();
    });
  });

  describe("modal close", () => {
    test("should call closeImportModal when cancel button is clicked", () => {
      const mockClose = jest.fn();
      render(
        <EntityImportModal {...defaultProps} closeImportModal={mockClose} />,
        { wrapper: TestWrapper },
      );

      // Cancel button should close the modal
      const cancelButton = screen.getByRole("button", { name: /キャンセル/i });
      fireEvent.click(cancelButton);
      expect(mockClose).toHaveBeenCalled();
    });
  });

  describe("form elements", () => {
    test("should render file input", () => {
      render(<EntityImportModal {...defaultProps} />, { wrapper: TestWrapper });

      // ImportForm should have a file input
      const fileInput = document.querySelector('input[type="file"]');
      expect(fileInput).toBeInTheDocument();
    });

    test("should render cancel button", () => {
      render(<EntityImportModal {...defaultProps} />, { wrapper: TestWrapper });

      // ImportForm should have a cancel button
      expect(
        screen.getByRole("button", { name: /キャンセル/i }),
      ).toBeInTheDocument();
    });
  });

  describe("import functionality", () => {
    test("should have import button", () => {
      render(<EntityImportModal {...defaultProps} />, { wrapper: TestWrapper });

      expect(
        screen.getByRole("button", { name: /インポート/i }),
      ).toBeInTheDocument();
    });
  });
});
