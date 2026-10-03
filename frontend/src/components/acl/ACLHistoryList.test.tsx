/**
 */

import { ACLHistory } from "@dmm-com/airone-apiclient-typescript-fetch";
import { act, render, screen, within } from "@testing-library/react";

import { ACLHistoryList } from "./ACLHistoryList";

import { TestWrapper } from "TestWrapper";
import i18n from "i18n/config";

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

  test("renders in English", async () => {
    await act(async () => {
      await i18n.changeLanguage("en");
    });

    render(<ACLHistoryList histories={histories} />, { wrapper: TestWrapper });

    expect(screen.getByText("Item")).toBeInTheDocument();
    expect(screen.getByText("Before")).toBeInTheDocument();
    expect(screen.getByText("After")).toBeInTheDocument();
    expect(screen.getByText("Time")).toBeInTheDocument();
    expect(screen.getByText("User")).toBeInTheDocument();
    expect(screen.getAllByText("Public setting").length).toBeGreaterThan(0);
    expect(screen.getByText("Public")).toBeInTheDocument();
    expect(screen.getByText("Limited public")).toBeInTheDocument();
  });
});
