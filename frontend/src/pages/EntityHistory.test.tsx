/**
 * @jest-environment jsdom
 */

import {
  render,
  waitForElementToBeRemoved,
  screen,
} from "@testing-library/react";
import React from "react";

import { EntityHistory } from "pages/EntityHistory";
import { TestWrapper } from "utils/TestWrapper";

afterEach(() => {
  jest.clearAllMocks();
});

test("should match snapshot", async () => {
  const entityHistory = [
    {
      operation: 1,
      time: "2022-01-01 00:00:00",
      user: {
        username: "aaa",
      },
      details: [
        {
          operation: 1,
          text: "aaa",
          target_obj: {
            name: "aaa",
          },
        },
      ],
    },
    {
      operation: 2,
      time: "2022-01-01 00:00:00",
      user: {
        username: "bbb",
      },
      details: [
        {
          operation: 2,
          text: "bbb",
          target_obj: {
            name: "bbb",
          },
        },
      ],
    },
  ];

  /* eslint-disable */
  jest
    .spyOn(require("../utils/AironeAPIClient"), "getEntityHistory")
    .mockResolvedValue({
      json() {
        return Promise.resolve(entityHistory);
      },
    });
  /* eslint-enable */

  // wait async calls and get rendered fragment
  const result = render(<EntityHistory />, {
    wrapper: TestWrapper,
  });
  await waitForElementToBeRemoved(screen.getByTestId("loading"));

  expect(result).toMatchSnapshot();
});
