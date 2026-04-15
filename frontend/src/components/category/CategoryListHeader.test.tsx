/**
 * @jest-environment jsdom
 */

import { CategoryList } from "@dmm-com/airone-apiclient-typescript-fetch";
import { render, screen } from "@testing-library/react";

import { CategoryListHeader } from "./CategoryListHeader";

import { TestWrapper } from "TestWrapper";
import { ACLType } from "services/ACLUtil";

describe("CategoryListHeader", () => {
  const createCategory = (permission: number): CategoryList => ({
    id: 1,
    name: "Test Category",
    note: "Test note",
    models: [],
    priority: 1,
    permission,
  });

  const defaultProps = {
    setToggle: jest.fn(),
  };

  describe("rendering", () => {
    test("should render category name", () => {
      render(
        <CategoryListHeader
          {...defaultProps}
          category={createCategory(ACLType.Full)}
        />,
        { wrapper: TestWrapper },
      );

      expect(screen.getByText("Test Category")).toBeInTheDocument();
    });
  });

  describe("menu button visibility", () => {
    test("menu button should be displayed when permission is Writable", () => {
      render(
        <CategoryListHeader
          {...defaultProps}
          category={createCategory(ACLType.Writable)}
        />,
        { wrapper: TestWrapper },
      );

      expect(screen.getByRole("button")).toBeInTheDocument();
    });

    test("menu button should be displayed when permission is Full", () => {
      render(
        <CategoryListHeader
          {...defaultProps}
          category={createCategory(ACLType.Full)}
        />,
        { wrapper: TestWrapper },
      );

      expect(screen.getByRole("button")).toBeInTheDocument();
    });

    test("menu button should not be displayed when permission is Readable", () => {
      render(
        <CategoryListHeader
          {...defaultProps}
          category={createCategory(ACLType.Readable)}
        />,
        { wrapper: TestWrapper },
      );

      expect(screen.queryByRole("button")).not.toBeInTheDocument();
    });

    test("menu button should not be displayed when permission is Nothing", () => {
      render(
        <CategoryListHeader
          {...defaultProps}
          category={createCategory(ACLType.Nothing)}
        />,
        { wrapper: TestWrapper },
      );

      expect(screen.queryByRole("button")).not.toBeInTheDocument();
    });
  });
});
