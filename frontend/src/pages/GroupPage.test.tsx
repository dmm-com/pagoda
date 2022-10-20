/**
 * @jest-environment jsdom
 */

import {
  render,
  waitForElementToBeRemoved,
  screen,
} from "@testing-library/react";
import React from "react";

import { GroupPage } from "pages/GroupPage";
import { TestWrapper } from "utils/TestWrapper";

afterEach(() => {
  jest.clearAllMocks();
});

test("should match snapshot", async () => {
  const groups = [
    {
      id: 1,
      name: "group1",
      children: [
        {
          id: 1,
          name: "group1",
          children: [],
        },
        {
          id: 2,
          name: "group2",
          children: [],
        },
      ],
    },
    {
      id: 2,
      name: "group2",
      children: [],
    },
  ];

  /* eslint-disable */
  jest
    .spyOn(
      require("../apiclient/AironeApiClientV2").aironeApiClientV2,
      "getGroupTrees"
    )
    .mockResolvedValue(Promise.resolve(groups));
  /* eslint-enable */

  // wait async calls and get rendered fragment
  const result = render(<GroupPage />, {
    wrapper: TestWrapper,
  });
  await waitForElementToBeRemoved(screen.getByTestId("loading"));

  expect(result).toMatchSnapshot();
});
