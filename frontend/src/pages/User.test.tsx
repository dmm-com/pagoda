/**
 * @jest-environment jsdom
 */

import {
  render,
  waitForElementToBeRemoved,
  screen,
} from "@testing-library/react";
import React from "react";

import { TestWrapper } from "../utils/TestWrapper";

import { User } from "./User";

afterEach(() => {
  jest.clearAllMocks();
});

test("should match snapshot", async () => {
  // TODO avoid to pass the global variable implicitly
  (window as any).django_context = {
    user: {
      is_superuser: false,
    },
  };

  const users = [
    {
      id: 1,
      username: "user1",
      email: "user1@example.com",
      date_joined: "2022-01-01 00:00:00",
    },
    {
      id: 2,
      username: "user2",
      email: "user2@example.com",
      date_joined: "2022-01-01 00:00:00",
    },
  ];

  /* eslint-disable */
  jest
    .spyOn(require("../utils/AironeAPIClient"), "getUsers")
    .mockResolvedValue({
      json() {
        return Promise.resolve(users);
      },
    });
  /* eslint-enable */

  // wait async calls and get rendered fragment
  const result = render(<User />, {
    wrapper: TestWrapper,
  });
  await waitForElementToBeRemoved(screen.getByTestId("loading"));

  expect(result).toMatchSnapshot();
});
