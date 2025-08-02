/**
 * @jest-environment jsdom
 */

import { render, screen } from "@testing-library/react";

import { TestWrapper } from "../../TestWrapper";
import { GroupTree } from "../../repository/AironeApiClient";
import { ServerContext } from "../../services/ServerContext";

import { GroupTreeRoot } from "./GroupTreeRoot";

// Mock for ServerContext
jest.mock("../../services/ServerContext", () => {
  const mockInstance = {
    user: { isSuperuser: false },
  };
  return {
    ServerContext: {
      getInstance: jest.fn(() => mockInstance),
    },
  };
});

describe("GroupTreeRoot", () => {
  const groups: GroupTree[] = [
    {
      id: 1,
      name: "group1",
      children: [
        {
          id: 2,
          name: "group2",
          children: [],
        },
        {
          id: 3,
          name: "group3",
          children: [],
        },
      ],
    },
    {
      id: 4,
      name: "group4",
      children: [],
    },
  ];

  const baseProps = {
    groupTrees: groups,
    selectedGroupId: 1,
    handleSelectGroupId: () => {},
    setGroupAnchorEls: () => {},
  };

  afterEach(() => {
    // Reset mock state after each test
    (ServerContext.getInstance as jest.Mock).mockReset();
  });

  test("renders correctly for general user (no menu buttons)", () => {
    // Mock as a general user
    (ServerContext.getInstance as jest.Mock).mockReturnValue({
      user: { isSuperuser: false },
    });

    render(<GroupTreeRoot {...baseProps} />, { wrapper: TestWrapper });

    expect(screen.getAllByRole("checkbox")).toHaveLength(4);
    expect(screen.getAllByRole("checkbox")[0]).toBeChecked();

    // General users should not see any action buttons
    expect(screen.queryAllByRole("button")).toHaveLength(0);
  });

  test("renders correctly for superuser (menu buttons shown)", () => {
    (ServerContext.getInstance as jest.Mock).mockReturnValue({
      user: { isSuperuser: true },
    });

    render(<GroupTreeRoot {...baseProps} />, { wrapper: TestWrapper });

    expect(screen.getAllByRole("checkbox")).toHaveLength(4);
    expect(screen.getAllByRole("checkbox")[0]).toBeChecked();

    // Superusers should see menu buttons for each group
    expect(screen.getAllByRole("button")).toHaveLength(4);
  });
});
