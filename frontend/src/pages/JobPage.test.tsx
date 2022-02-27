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
  const jobs = [
    {
      id: 1,
      operation: 1,
      status: 1,
      passedTime: "2022-01-01 00:00:00",
      createdCt: "2022-01-01 00:00:00",
      text: "text",
      target: {
        name: "target1",
      },
    },
    {
      id: 2,
      operation: 2,
      status: 2,
      passedTime: "2022-01-01 00:00:00",
      createdAt: "2022-01-01 00:00:00",
      text: "text",
      target: {
        name: "target2",
      },
    },
  ];

  /* eslint-disable */
  jest
    .spyOn(require("apiclient/AironeApiClientV2").aironeApiClientV2, "getJobs")
    .mockResolvedValue(Promise.resolve(jobs));
  /* eslint-enable */

  // wait async calls and get rendered fragment
  const result = render(<JobPage />, {
    wrapper: TestWrapper,
  });
  await waitForElementToBeRemoved(screen.getByTestId("loading"));

  expect(result).toMatchSnapshot();
});
