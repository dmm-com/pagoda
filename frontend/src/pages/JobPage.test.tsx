/**
 * @jest-environment jsdom
 */

import {
  render,
  waitForElementToBeRemoved,
  screen,
} from "@testing-library/react";
import React from "react";

import { JobPage } from "pages/JobPage";
import { TestWrapper } from "utils/TestWrapper";

afterEach(() => {
  jest.clearAllMocks();
});

test("should match snapshot", async () => {
  const groups = [
    {
      id: 1,
      operation: 1,
      status: 1,
      passed_time: "2022-01-01 00:00:00",
      created_at: "2022-01-01 00:00:00",
      note: "note",
      target: {
        name: "target1",
      },
    },
    {
      id: 2,
      operation: 2,
      status: 2,
      passed_time: "2022-01-01 00:00:00",
      created_at: "2022-01-01 00:00:00",
      note: "note",
      target: {
        name: "target2",
      },
    },
  ];

  /* eslint-disable */
  jest.spyOn(require("../utils/AironeAPIClient"), "getJobs").mockResolvedValue({
    json() {
      return Promise.resolve(groups);
    },
  });
  /* eslint-enable */

  // wait async calls and get rendered fragment
  const result = render(<JobPage />, {
    wrapper: TestWrapper,
  });
  await waitForElementToBeRemoved(screen.getByTestId("loading"));

  expect(result).toMatchSnapshot();
});
