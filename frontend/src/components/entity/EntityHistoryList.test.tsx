/**
 * @jest-environment jsdom
 */

import { PaginatedEntityHistoryList } from "@dmm-com/airone-apiclient-typescript-fetch";
import { render, screen, within } from "@testing-library/react";

import { EntityHistoryList, TargetOperation } from "./EntityHistoryList";

import { TestWrapper } from "TestWrapper";

describe("EntityHistoryList", () => {
  const histories: PaginatedEntityHistoryList = {
    count: 6,
    results: [
      {
        operation: TargetOperation.ADD_ENTITY,
        time: new Date("2020/01/01 00:00:00"),
        username: "user1",
        text: "entity1",
        targetObj: "entity1",
        isDetail: false,
        changes: [
          { action: "create", target: "name", before: null, after: "entity1" },
        ],
      },
      {
        operation: TargetOperation.MOD_ENTITY,
        time: new Date("2020/01/02 00:00:00"),
        username: "user2",
        text: "entity1",
        targetObj: "entity1",
        isDetail: false,
        changes: [
          {
            action: "update",
            target: "name",
            before: "old_entity1",
            after: "entity1",
          },
        ],
      },
      {
        operation: TargetOperation.ADD_ATTR,
        time: new Date("2020/01/03 00:00:00"),
        username: "user3",
        text: "entity1",
        targetObj: "attr1",
        isDetail: false,
        changes: [
          { action: "create", target: "name", before: null, after: "attr1" },
        ],
      },
      {
        operation: TargetOperation.MOD_ATTR,
        time: new Date("2020/01/04 00:00:00"),
        username: "user4",
        text: "entity1",
        targetObj: "attr1",
        isDetail: false,
        changes: [
          {
            action: "update",
            target: "is_mandatory",
            before: false,
            after: true,
          },
        ],
      },
      {
        operation: TargetOperation.DEL_ATTR,
        time: new Date("2020/01/05 00:00:00"),
        username: "user5",
        text: "entity1",
        targetObj: "attr1_deleted_20200105000000",
        isDetail: false,
        changes: [],
      },
      {
        operation: TargetOperation.DEL_ENTITY,
        time: new Date("2020/01/06 00:00:00"),
        username: "user6",
        text: "entity1",
        targetObj: "entity1",
        isDetail: false,
        changes: [
          { action: "delete", target: "name", before: "entity1", after: null },
        ],
      },
    ],
  };

  test("should render entity histories", () => {
    const changePage = jest.fn();

    render(
      <EntityHistoryList
        histories={histories}
        page={1}
        changePage={changePage}
      />,
      { wrapper: TestWrapper },
    );

    const tableBody = screen.getAllByRole("rowgroup")[1];
    const historyRows = within(tableBody).getAllByRole("row");
    expect(historyRows).toHaveLength(6);

    // ADD_ENTITY: shows "作成" and changes in after column
    expect(within(historyRows[0]).queryByText("作成")).toBeInTheDocument();
    expect(within(historyRows[0]).queryByText("name:")).toBeInTheDocument();
    expect(within(historyRows[0]).queryByText("entity1")).toBeInTheDocument();

    // MOD_ENTITY: shows "変更" and changes in before/after columns
    expect(within(historyRows[1]).queryByText("変更")).toBeInTheDocument();
    expect(
      within(historyRows[1]).queryByText("old_entity1"),
    ).toBeInTheDocument();

    // ADD_ATTR: shows "属性追加" and targetObj
    expect(within(historyRows[2]).queryByText("属性追加")).toBeInTheDocument();
    expect(within(historyRows[2]).queryByText("attr1")).toBeInTheDocument();

    // MOD_ATTR: shows "属性変更" and changes from simple-history
    expect(within(historyRows[3]).queryByText("属性変更")).toBeInTheDocument();
    // The changes display shows "is_mandatory" as a target field and "true" as the after value
    expect(
      within(historyRows[3]).queryAllByText(/is_mandatory/).length,
    ).toBeGreaterThan(0);
    expect(
      within(historyRows[3]).queryAllByText(/true/).length,
    ).toBeGreaterThan(0);

    // DEL_ATTR: shows "属性削除" and targetObj (with _deleted_ suffix removed)
    expect(within(historyRows[4]).queryByText("属性削除")).toBeInTheDocument();
    expect(within(historyRows[4]).queryAllByText("attr1")).toHaveLength(2);

    // DEL_ENTITY: shows "削除" and changes
    expect(within(historyRows[5]).queryByText("削除")).toBeInTheDocument();
  });
});
