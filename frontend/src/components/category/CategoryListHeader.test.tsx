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
          isEdit={true}
        />,
        { wrapper: TestWrapper },
      );

      expect(screen.getByText("Test Category")).toBeInTheDocument();
    });
  });

  describe("menu button visibility", () => {
    describe("when isEdit is true", () => {
      test("menu button should be displayed when permission is Writable", () => {
        render(
          <CategoryListHeader
            {...defaultProps}
            category={createCategory(ACLType.Writable)}
            isEdit={true}
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
            isEdit={true}
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
            isEdit={true}
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
            isEdit={true}
          />,
          { wrapper: TestWrapper },
        );

        expect(screen.queryByRole("button")).not.toBeInTheDocument();
      });
    });

    describe("when isEdit is false", () => {
      test("menu button should not be displayed even with Full permission", () => {
        render(
          <CategoryListHeader
            {...defaultProps}
            category={createCategory(ACLType.Full)}
            isEdit={false}
          />,
          { wrapper: TestWrapper },
        );

        expect(screen.queryByRole("button")).not.toBeInTheDocument();
      });

      test("menu button should not be displayed with Writable permission", () => {
        render(
          <CategoryListHeader
            {...defaultProps}
            category={createCategory(ACLType.Writable)}
            isEdit={false}
          />,
          { wrapper: TestWrapper },
        );

        expect(screen.queryByRole("button")).not.toBeInTheDocument();
      });
    });
  });
});
