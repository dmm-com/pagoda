/**
 * @jest-environment jsdom
 */

import { render, screen } from "@testing-library/react";
import React from "react";

import { TestWrapper } from "../../TestWrapper";
import { GroupTree } from "../../repository/AironeApiClient";

import { GroupTreeRoot } from "./GroupTreeRoot";

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

  test("should show groups", async function () {
    render(
      <GroupTreeRoot
        groupTrees={groups}
        selectedGroupId={1}
        handleSelectGroupId={() => {
          /* noop */
        }}
        setGroupAnchorEls={() => {
          /* noop */
        }}
      />,
      { wrapper: TestWrapper }
    );

    expect(screen.getAllByRole("checkbox")).toHaveLength(4);
    expect(screen.getAllByRole("checkbox")[0]).toBeChecked();
    expect(screen.getAllByRole("button")).toHaveLength(4);
  });
});
