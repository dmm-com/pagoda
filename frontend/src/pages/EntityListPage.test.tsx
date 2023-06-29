/**
 * @jest-environment jsdom
 */

import {
  render,
  waitForElementToBeRemoved,
  screen,
} from "@testing-library/react";
import React from "react";

import { TestWrapper } from "TestWrapper";
import { EntityListPage } from "pages/EntityListPage";

afterEach(() => {
  jest.clearAllMocks();
});

test("should match snapshot", async () => {
  const entities = [
    {
      id: 1,
      name: "aaa",
      note: "",
      isToplevel: false,
      attrs: [],
    },
    {
      id: 2,
      name: "aaaaa",
      note: "",
      isToplevel: false,
      attrs: [],
    },
    {
      id: 3,
      name: "bbbbb",
      note: "",
      isToplevel: false,
      attrs: [],
    },
  ];

  /* eslint-disable */
  jest
    .spyOn(
      require("../repository/AironeApiClientV2").aironeApiClientV2,
      "getEntities"
    )
    .mockResolvedValue(Promise.resolve({ results: entities }));
  /* eslint-enable */

  // wait async calls and get rendered fragment
  const result = render(<EntityListPage />, {
    wrapper: TestWrapper,
  });
  await waitForElementToBeRemoved(screen.getByTestId("loading"));

  expect(result).toMatchSnapshot();
});
