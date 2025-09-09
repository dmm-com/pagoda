/**
 * @jest-environment jsdom
 */

import { act, render, screen, within } from "@testing-library/react";

import {
  EntryAttributeTypeTypeEnum,
  PaginatedEntryHistoryAttributeValueList,
} from "@dmm-com/airone-apiclient-typescript-fetch";
import { TestWrapper } from "TestWrapper";
import { EntryHistoryList } from "components/entry/EntryHistoryList";

describe("EntryHistoryList", () => {
  const histories: PaginatedEntryHistoryAttributeValueList = {
    count: 2,
    results: [
      {
        id: 1,
        type: EntryAttributeTypeTypeEnum.STRING,
        parentAttr: {
          id: 1,
          name: "string",
        },
        currValue: {
          asString: "value2",
        },
        prevValue: {
          asString: "value1",
        },
        prevId: null,
        createdUser: "user2",
        createdTime: new Date("2020-01-02T00:00:00Z"),
      },
      {
        id: 2,
        type: EntryAttributeTypeTypeEnum.STRING,
        parentAttr: {
          id: 1,
          name: "string",
        },
        currValue: {
          asString: "value1",
        },
        prevValue: {},
        prevId: null,
        createdUser: "user1",
        createdTime: new Date("2020-01-01T00:00:00Z"),
      },
    ],
  };

  test("should render entry histories", async () => {
    await act(async () => {
      render(
        <EntryHistoryList
          entityId={2}
          entryId={1}
          histories={histories}
          page={1}
          changePage={() => {
            /* do nothing */
          }}
        />,
        { wrapper: TestWrapper },
      );
    });

    // 0 is header, 1 is body
    const bodyRowGroup = screen.getAllByRole("rowgroup")[1];
    expect(within(bodyRowGroup).queryAllByRole("row")).toHaveLength(2);
    expect(within(bodyRowGroup).queryAllByText("value1")).toHaveLength(2);
    expect(within(bodyRowGroup).queryByText("value2")).toBeInTheDocument();
  });
});
