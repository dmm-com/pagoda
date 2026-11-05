/**
 */

import { render, screen } from "@testing-library/react";

import { TestWrapper } from "../../TestWrapper";
import { GroupTree } from "../../repository/AironeApiClient";
import { ServerContext } from "../../services/ServerContext";

import { GroupTreeRoot } from "./GroupTreeRoot";

import type { Mock } from "vitest";

// Mock for ServerContext
vi.mock("../../services/ServerContext", () => {
  const mockInstance = {
    user: { isSuperuser: false },
  };
  return {
    ServerContext: {
      getInstance: vi.fn(() => mockInstance),
    },
  };
});

describe("GroupTreeRoot", () => {
  const groups: GroupTree[] = [
    {
      id: 1,
      name: "group1",
      displayName: "Group One",
      children: [
        {
          id: 2,
          name: "group2",
          displayName: "Group Two",
          children: [],
        },
        {
          id: 3,
          name: "group3",
          displayName: "Group Three",
          children: [],
        },
      ],
    },
    {
      id: 4,
      name: "group4",
      displayName: "",
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
    (ServerContext.getInstance as Mock).mockReset();
  });

  test("renders correctly for general user (no menu buttons)", () => {
    // Mock as a general user
    (ServerContext.getInstance as Mock).mockReturnValue({
      user: { isSuperuser: false },
    });

    render(<GroupTreeRoot {...baseProps} />, { wrapper: TestWrapper });

    expect(screen.getAllByRole("checkbox")).toHaveLength(4);
    expect(screen.getAllByRole("checkbox")[0]).toBeChecked();

    // General users should not see any action buttons
    expect(screen.queryAllByRole("button")).toHaveLength(0);
  });

  test("uses display names and keeps full names available as titles", () => {
    (ServerContext.getInstance as Mock).mockReturnValue({
      user: { isSuperuser: false },
    });

    render(
      <GroupTreeRoot
        {...baseProps}
        groupTrees={[
          {
            id: 10,
            name: "organization / team-a",
            displayName: "Team",
            children: [],
          },
          {
            id: 11,
            name: "organization / team-b",
            displayName: "Team",
            children: [],
          },
          {
            id: 12,
            name: "organization / team-c",
            displayName: "",
            children: [],
          },
        ]}
      />,
      { wrapper: TestWrapper },
    );

    expect(screen.getAllByText("Team")).toHaveLength(2);
    expect(screen.getByText("organization / team-c")).toBeInTheDocument();
    expect(screen.getByTitle("organization / team-a")).toBeInTheDocument();
    expect(screen.getByTitle("organization / team-b")).toBeInTheDocument();
  });

  test("renders correctly for superuser (menu buttons shown)", () => {
    (ServerContext.getInstance as Mock).mockReturnValue({
      user: { isSuperuser: true },
    });

    render(<GroupTreeRoot {...baseProps} />, { wrapper: TestWrapper });

    expect(screen.getAllByRole("checkbox")).toHaveLength(4);
    expect(screen.getAllByRole("checkbox")[0]).toBeChecked();

    // Superusers should see menu buttons for each group
    expect(screen.getAllByRole("button")).toHaveLength(4);
  });
});
