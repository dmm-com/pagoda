/**
 * @jest-environment jsdom
 */

import {
  render,
  waitForElementToBeRemoved,
  screen,
} from "@testing-library/react";
import React from "react";

import { Search } from "pages/Search";
import { TestWrapper } from "utils/TestWrapper";

afterEach(() => {
  jest.clearAllMocks();
});

test("should match snapshot", async () => {
  const searchEntries = [
    {
      id: 1,
      name: "aaa",
    },
    {
      id: 2,
      name: "aaaaa",
    },
  ];

  /* eslint-disable */
  jest
    .spyOn(require("../utils/AironeAPIClient"), "getEntrySearch")
    .mockResolvedValue({
      json() {
        return Promise.resolve(searchEntries);
      },
    });
  jest.spyOn(URLSearchParams.prototype, "get").mockReturnValue("aaa");
  /* eslint-enable */

  // wait async calls and get rendered fragment
  const result = render(<Search />, {
    wrapper: TestWrapper,
  });
  await waitForElementToBeRemoved(screen.getByTestId("loading"));

  expect(result).toMatchSnapshot();
});
