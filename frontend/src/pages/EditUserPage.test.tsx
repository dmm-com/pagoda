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
import { EditUserPage } from "pages/EditUserPage";

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

  const user = {
    id: 1,
    username: "user1",
    email: "user1@example.com",
    is_superuser: false,
  };

  /* eslint-disable */
  jest
    .spyOn(require("../repository/AironeApiClient").aironeApiClient, "getUser")
    .mockResolvedValue(Promise.resolve(user));
  /* eslint-enable */

  // wait async calls and get rendered fragment
  const result = render(<EditUserPage />, {
    wrapper: TestWrapper,
  });
  await waitForElementToBeRemoved(screen.getByTestId("loading"));

  expect(result).toMatchSnapshot();
});
