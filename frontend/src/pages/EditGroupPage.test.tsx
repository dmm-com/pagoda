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
import { EditGroupPage } from "pages/EditGroupPage";

afterEach(() => {
  jest.clearAllMocks();
});

test("should match snapshot", async () => {
  Object.defineProperty(window, "django_context", {
    value: {
      user: {
        isSuperuser: true,
      },
    },
    writable: false,
  });

  const users = {
    count: 2,
    next: null,
    previous: null,
    results: [
      {
        id: 1,
        username: "user1",
        email: "user1@example.com",
        is_superuser: false,
      },
      {
        id: 2,
        username: "user2",
        email: "user2@example.com",
        is_superuser: false,
      },
    ],
  };

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
      require("../repository/AironeApiClientV2").aironeApiClientV2,
      "getUsers"
    )
    .mockResolvedValue(Promise.resolve(users));
  jest
    .spyOn(
      require("../repository/AironeApiClientV2").aironeApiClientV2,
      "getGroup"
    )
    .mockResolvedValue(Promise.resolve(group));
  jest
    .spyOn(
      require("../repository/AironeApiClientV2").aironeApiClientV2,
      "getGroupTrees"
    )
    .mockResolvedValue(Promise.resolve(groups));
  /* eslint-enable */

  // wait async calls and get rendered fragment
  const result = render(<EditGroupPage />, {
    wrapper: TestWrapper,
  });
  await waitForElementToBeRemoved(screen.getByTestId("loading"));

  expect(result).toMatchSnapshot();
});
