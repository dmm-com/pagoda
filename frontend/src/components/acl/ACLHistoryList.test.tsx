/**
 * @jest-environment jsdom
 */

import { ACLHistory } from "@dmm-com/airone-apiclient-typescript-fetch";
import { render, screen, within } from "@testing-library/react";
import React from "react";

import { ACLHistoryList } from "./ACLHistoryList";

import { TestWrapper } from "TestWrapper";

describe("ACLHistoryList", () => {
  const histories: ACLHistory[] = [
    {
      user: {
        id: 1,
        username: "user1",
      },
      time: new Date("2020/01/01 00:00:00"),
      name: "attr1",
      changes: [
        {
          action: "create",
          target: "is_public",
          before: null,
          after: false,
        },
      ],
    },
    {
      user: {
        id: 1,
        username: "user1",
      },
      time: new Date("2020/01/01 00:00:00"),
      name: "attr1",
      changes: [
        {
          action: "update",
          target: "is_public",
          before: false,
          after: true,
        },
      ],
    },
  ];

  test("should render acl histories", () => {
    render(<ACLHistoryList histories={histories} />, { wrapper: TestWrapper });

    const bodyRowGroup = screen.getAllByRole("rowgroup")[1];
    expect(within(bodyRowGroup).queryAllByRole("row")).toHaveLength(4);
  });
});
