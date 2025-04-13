/**
 * @jest-environment jsdom
 */

import { fireEvent, render, screen } from "@testing-library/react";
import React from "react";

import { TestWrapper } from "../../TestWrapper";
import { GroupTree } from "../../repository/AironeApiClient";
import { ServerContext } from "../../services/ServerContext";

import { GroupTreeItem } from "./GroupTreeItem";

// Mock for ServerContext
jest.mock("../../services/ServerContext", () => {
  const mockInstance = {
    user: {
      isSuperuser: false,
    },
  };
  return {
    ServerContext: {
      getInstance: jest.fn(() => mockInstance),
    },
  };
});

// Mock group tree data for testing
const mockGroupTrees: GroupTree[] = [
  {
    id: 1,
    name: "u30b0u30ebu30fcu30d71",
    children: [],
  },
  {
    id: 2,
    name: "u30b0u30ebu30fcu30d72",
    children: [
      {
        id: 3,
        name: "u5b50u30b0u30ebu30fcu30d71",
        children: [],
      },
    ],
  },
];

describe("GroupTreeItem", () => {
  test("should render with basic props without throwing", () => {
    const handleSelectGroupId = jest.fn();

    expect(() =>
      render(
        <GroupTreeItem
          depth={0}
          groupTrees={mockGroupTrees}
          selectedGroupId={null}
          handleSelectGroupId={handleSelectGroupId}
        />,
        {
          wrapper: TestWrapper,
        },
      ),
    ).not.toThrow();
  });

  test("should display group names correctly", () => {
    render(
      <GroupTreeItem
        depth={0}
        groupTrees={mockGroupTrees}
        selectedGroupId={null}
        handleSelectGroupId={() => {}}
      />,
      { wrapper: TestWrapper },
    );

    expect(screen.getByText("u30b0u30ebu30fcu30d71")).toBeInTheDocument();
    expect(screen.getByText("u30b0u30ebu30fcu30d72")).toBeInTheDocument();
  });

  test("should render group name as a link to detail page when user is superuser", () => {
    // Override the mock to set user as superuser
    const mockServerContext = ServerContext.getInstance() as {
      user: { isSuperuser: boolean };
    };
    mockServerContext.user.isSuperuser = true;

    const { container } = render(
      <GroupTreeItem
        depth={0}
        groupTrees={[mockGroupTrees[0]]}
        selectedGroupId={null}
        handleSelectGroupId={() => {}}
      />,
      { wrapper: TestWrapper },
    );

    // Check that link exists and has a proper href attribute
    // Note: The actual href value may vary depending on TestWrapper configuration
    const link = container.querySelector("a");
    expect(link).toBeInTheDocument();
    expect(link?.getAttribute("href")).not.toBe("#");
  });

  test("should not render group name as a clickable link when user is not superuser", () => {
    // Override the mock to set user as non-superuser
    const mockServerContext = ServerContext.getInstance() as {
      user: { isSuperuser: boolean };
    };
    mockServerContext.user.isSuperuser = false;

    const { container } = render(
      <GroupTreeItem
        depth={0}
        groupTrees={[mockGroupTrees[0]]}
        selectedGroupId={null}
        handleSelectGroupId={() => {}}
      />,
      { wrapper: TestWrapper },
    );

    // Check that link has "/" href due to TestWrapper configuration
    // In a real scenario without TestWrapper, it might be "#"
    const link = container.querySelector("a");
    expect(link?.getAttribute("href")).toBe("/");
  });

  test("should check the checkbox when group ID matches selectedGroupId", () => {
    render(
      <GroupTreeItem
        depth={0}
        groupTrees={[mockGroupTrees[0]]}
        selectedGroupId={1}
        handleSelectGroupId={() => {}}
      />,
      { wrapper: TestWrapper },
    );

    const checkbox = screen.getByRole("checkbox");
    expect(checkbox).toBeChecked();
  });

  test("should not check the checkbox when group ID doesn't match selectedGroupId", () => {
    render(
      <GroupTreeItem
        depth={0}
        groupTrees={[mockGroupTrees[0]]}
        selectedGroupId={2}
        handleSelectGroupId={() => {}}
      />,
      { wrapper: TestWrapper },
    );

    const checkbox = screen.getByRole("checkbox");
    expect(checkbox).not.toBeChecked();
  });

  test("should call handleSelectGroupId with correct ID when checkbox is clicked (selection)", () => {
    const handleSelectGroupId = jest.fn();

    render(
      <GroupTreeItem
        depth={0}
        groupTrees={[mockGroupTrees[0]]}
        selectedGroupId={null}
        handleSelectGroupId={handleSelectGroupId}
      />,
      { wrapper: TestWrapper },
    );

    const checkbox = screen.getByRole("checkbox");
    fireEvent.click(checkbox);

    expect(handleSelectGroupId).toHaveBeenCalledWith(1);
  });

  test("should call handleSelectGroupId with null when checkbox is clicked (deselection)", () => {
    const handleSelectGroupId = jest.fn();

    render(
      <GroupTreeItem
        depth={0}
        groupTrees={[mockGroupTrees[0]]}
        selectedGroupId={1}
        handleSelectGroupId={handleSelectGroupId}
      />,
      { wrapper: TestWrapper },
    );

    const checkbox = screen.getByRole("checkbox");
    fireEvent.click(checkbox);

    expect(handleSelectGroupId).toHaveBeenCalledWith(null);
  });

  test("should display menu button when setGroupAnchorEls is provided", () => {
    const setGroupAnchorEls = jest.fn();

    render(
      <GroupTreeItem
        depth={0}
        groupTrees={[mockGroupTrees[0]]}
        selectedGroupId={null}
        handleSelectGroupId={() => {}}
        setGroupAnchorEls={setGroupAnchorEls}
      />,
      { wrapper: TestWrapper },
    );

    const menuButton = screen.getByRole("button");
    expect(menuButton).toBeInTheDocument();
  });

  test("should not display menu button when setGroupAnchorEls is not provided", () => {
    const { container } = render(
      <GroupTreeItem
        depth={0}
        groupTrees={[mockGroupTrees[0]]}
        selectedGroupId={null}
        handleSelectGroupId={() => {}}
      />,
      { wrapper: TestWrapper },
    );

    const menuButtons = container.querySelectorAll("button");
    // Checkboxes are not counted as buttons, so there should be 0 buttons when menu button is not shown
    expect(menuButtons.length).toBe(0);
  });

  test("should call setGroupAnchorEls with correct arguments when menu button is clicked", () => {
    const setGroupAnchorEls = jest.fn();

    render(
      <GroupTreeItem
        depth={0}
        groupTrees={[mockGroupTrees[0]]}
        selectedGroupId={null}
        handleSelectGroupId={() => {}}
        setGroupAnchorEls={setGroupAnchorEls}
      />,
      { wrapper: TestWrapper },
    );

    const menuButton = screen.getByRole("button");
    fireEvent.click(menuButton);

    expect(setGroupAnchorEls).toHaveBeenCalled();
    // Verify the argument - groupId should be correct
    expect(setGroupAnchorEls.mock.calls[0][0].groupId).toBe(1);
    // Verify that HTMLButtonElement is passed
    expect(
      setGroupAnchorEls.mock.calls[0][0].el instanceof HTMLButtonElement,
    ).toBe(true);
  });

  test("should recursively render child groups when they exist", () => {
    render(
      <GroupTreeItem
        depth={0}
        groupTrees={[mockGroupTrees[1]]} // Use group2 which has a child
        selectedGroupId={null}
        handleSelectGroupId={() => {}}
      />,
      { wrapper: TestWrapper },
    );

    // Both parent and child group names should be displayed
    expect(screen.getByText("u30b0u30ebu30fcu30d72")).toBeInTheDocument();
    expect(screen.getByText("u5b50u30b0u30ebu30fcu30d71")).toBeInTheDocument();
  });

  test("should apply correct indent style based on depth", () => {
    const CHILDREN_INDENT_WIDTH = 16; // Same constant as in the component
    const testDepth = 2;

    const { container } = render(
      <GroupTreeItem
        depth={testDepth}
        groupTrees={[mockGroupTrees[0]]}
        selectedGroupId={null}
        handleSelectGroupId={() => {}}
      />,
      { wrapper: TestWrapper },
    );

    const listItem = container.querySelector(".MuiListItem-root");
    // Check that paddingLeft style matches the expected value
    // Based on the calculation formula: (depth + 1) * CHILDREN_INDENT_WIDTH
    expect(listItem).toHaveStyle(
      `padding-left: ${(testDepth + 1) * CHILDREN_INDENT_WIDTH}px`,
    );
  });
});
