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
import { UserListPage } from "pages/UserListPage";

afterEach(() => {
  jest.clearAllMocks();
});

test("should match snapshot", async () => {
  Object.defineProperty(window, "django_context", {
    value: {
      user: {
        is_superuser: false,
      },
    },
    writable: false,
  });

  const users = {
    count: 1,
    next: null,
    previous: null,
    results: [
      {
        id: 1,
        username: "user1",
        email: "user1@example.com",
        is_superuser: false,
      },
    ],
  };

  /* eslint-disable */
  jest
    .spyOn(require("../repository/AironeApiClient").aironeApiClient, "getUsers")
    .mockResolvedValue(Promise.resolve(users));
  /* eslint-enable */

  // wait async calls and get rendered fragment
  const result = render(<UserListPage />, {
    wrapper: TestWrapper,
  });
  await waitForElementToBeRemoved(screen.getByTestId("loading"));

  expect(result).toMatchSnapshot();
});
