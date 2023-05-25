/**
 * @jest-environment jsdom
 */

import {
  render,
  waitForElementToBeRemoved,
  screen,
} from "@testing-library/react";
import React from "react";
import { MemoryRouter, Route } from "react-router-dom";

import { showEntryHistoryPath } from "../Routes";

import { EntryHistoryListPage } from "./EntryHistoryListPage";

import { TestWrapper } from "TestWrapper";

afterEach(() => {
  jest.clearAllMocks();
});

test("should match snapshot", async () => {
  const entry = {
    id: 1,
    name: "aaa",
    isActive: true,
    schema: {
      id: 2,
      name: "bbb",
    },
    attrs: [],
  };

  const histories = {
    count: 0,
    results: [],
  };

  /* eslint-disable */
  jest
    .spyOn(
      require("repository/AironeApiClientV2").aironeApiClientV2,
      "getEntry"
    )
    .mockResolvedValue(Promise.resolve(entry));

  jest
    .spyOn(
      require("repository/AironeApiClientV2").aironeApiClientV2,
      "getEntryHistories"
    )
    .mockResolvedValue(Promise.resolve(histories));
  /* eslint-enable */

  // wait async calls and get rendered fragment
  const result = render(
    <MemoryRouter initialEntries={[showEntryHistoryPath(2, 1)]}>
      <Route
        path={showEntryHistoryPath(":entityId", ":entryId")}
        component={EntryHistoryListPage}
      />
    </MemoryRouter>,
    {
      wrapper: TestWrapper,
    }
  );
  await waitForElementToBeRemoved(screen.getByTestId("loading"));

  expect(result).toMatchSnapshot();

  jest.clearAllMocks();
});
