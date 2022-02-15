/**
 * @jest-environment jsdom
 */

import {
  render,
  waitForElementToBeRemoved,
  screen,
} from "@testing-library/react";
import React from "react";

import { EditGroupPage } from "pages/EditGroupPage";
import { TestWrapper } from "utils/TestWrapper";

afterEach(() => {
  jest.clearAllMocks();
});

test("should match snapshot", async () => {
  const users = [
    {
      id: 1,
      username: "user1",
    },
    {
      id: 2,
      username: "user2",
    },
  ];
  const group = {
    id: 1,
    name: "group1",
    members: [
      {
        id: 1,
        username: "user1",
      },
    ],
  };

  /* eslint-disable */
  jest
    .spyOn(require("../utils/AironeAPIClient"), "getUsers")
    .mockResolvedValue({
      json() {
        return Promise.resolve(users);
      },
    });
  jest
    .spyOn(
      require("../apiclient/AironeApiClientV2").aironeApiClientV2,
      "getGroup"
    )
    .mockResolvedValue(Promise.resolve(group));
  /* eslint-enable */

  // wait async calls and get rendered fragment
  const result = render(<EditGroupPage />, {
    wrapper: TestWrapper,
  });
  await waitForElementToBeRemoved(screen.getByTestId("loading"));

  expect(result).toMatchSnapshot();
});
