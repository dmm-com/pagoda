/**
 * @jest-environment jsdom
 */

import { PaginatedEntityHistoryList } from "@dmm-com/airone-apiclient-typescript-fetch";
import {
  render,
  waitForElementToBeRemoved,
  screen,
} from "@testing-library/react";
import React from "react";

import { TestWrapper } from "TestWrapper";
import { EntityHistoryPage } from "pages/EntityHistoryPage";

afterEach(() => {
  jest.clearAllMocks();
});

test("should match snapshot", async () => {
  const entity = {
    id: 1,
    name: "aaa",
    note: "",
    isToplevel: false,
    attrs: [],
  };
  const histories: PaginatedEntityHistoryList = {
    count: 1,
    results: [
      {
        operation: 1,
        time: new Date(2022, 0, 1, 0, 0, 0),
        username: "aaa",
        targetObj: "aaa",
        text: "text",
        isDetail: false,
      },
      {
        operation: 1,
        time: new Date(2022, 0, 1, 0, 0, 0),
        username: "bbb",
        targetObj: "bbb",
        text: "text",
        isDetail: false,
      },
    ],
  };

  /* eslint-disable */
  jest
    .spyOn(
      require("../repository/AironeApiClient").aironeApiClient,
      "getEntity"
    )
    .mockResolvedValue(Promise.resolve(entity));
  jest
    .spyOn(
      require("../repository/AironeApiClient").aironeApiClient,
      "getEntityHistories"
    )
    .mockResolvedValue(Promise.resolve(histories));
  /* eslint-enable */

  // wait async calls and get rendered fragment
  const result = render(<EntityHistoryPage />, {
    wrapper: TestWrapper,
  });
  await waitForElementToBeRemoved(screen.getByTestId("loading"));

  expect(result).toMatchSnapshot();
});
