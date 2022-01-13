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

import { EditUser } from "./EditUser";

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

  const user = {
    id: 1,
    username: "user1",
    email: "user1@example.com",
    is_superuser: false,
  };

  /* eslint-disable */
  jest.spyOn(require("../utils/AironeAPIClient"), "getUser").mockResolvedValue({
    json() {
      return Promise.resolve(user);
    },
  });
  /* eslint-enable */

  // wait async calls and get rendered fragment
  const result = render(<EditUser />, {
    wrapper: TestWrapper,
  });
  await waitForElementToBeRemoved(screen.getByTestId("loading"));

  expect(result).toMatchSnapshot();
});
