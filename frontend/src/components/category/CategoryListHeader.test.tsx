/**
 * @jest-environment jsdom
 */

import { render, screen, fireEvent } from "@testing-library/react";
import React from "react";

import { CategoryListHeader } from "./CategoryListHeader";

import { TestWrapper } from "TestWrapper";

describe("CategoryListHeader", () => {
  // dummy category data for testing
  const mockCategory = {
    id: 1,
    name: "Test Category",
    models: [],
    note: "",
    priority: 0,
  };

  test("should render category name", () => {
    render(
      <CategoryListHeader
        category={mockCategory}
        isEdit={false}
        setToggle={() => {}}
      />,
      { wrapper: TestWrapper },
    );

    // category name should be displayed
    expect(screen.getByText("Test Category")).toBeInTheDocument();
  });

  test("should not render control menu when isEdit is false", () => {
    const { container } = render(
      <CategoryListHeader
        category={mockCategory}
        isEdit={false}
        setToggle={() => {}}
      />,
      { wrapper: TestWrapper },
    );

    // MoreVertIcon button should not be present
    const iconButtons = container.querySelectorAll("button");
    expect(iconButtons.length).toBe(0);
  });

  test("should render control menu when isEdit is true", () => {
    const { container } = render(
      <CategoryListHeader
        category={mockCategory}
        isEdit={true}
        setToggle={() => {}}
      />,
      { wrapper: TestWrapper },
    );

    // MoreVertIcon button should be present
    const iconButtons = container.querySelectorAll("button");
    expect(iconButtons.length).toBe(1);
  });

  test("clicking the menu button should open the CategoryControlMenu", () => {
    render(
      <CategoryListHeader
        category={mockCategory}
        isEdit={true}
        setToggle={() => {}}
      />,
      { wrapper: TestWrapper },
    );

    // Find and click the menu button
    const menuButton = screen.getByRole("button");
    fireEvent.click(menuButton);

    // Verify that the menu is open (an element with role="menu" exists)
    const menu = screen.getByRole("menu");
    expect(menu).toBeInTheDocument();

    // Verify menu items
    expect(screen.getByText("編集")).toBeInTheDocument();
    expect(screen.getByText("ACL 設定")).toBeInTheDocument();
    expect(screen.getByText("削除")).toBeInTheDocument();
  });
});
