/**
 * @jest-environment jsdom
 */

import {
  render,
  waitForElementToBeRemoved,
  screen,
} from "@testing-library/react";
import React from "react";

import { EditUserPasswordPage } from "pages/EditUserPasswordPage";
import { TestWrapper } from "utils/TestWrapper";

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
  };

  /* eslint-disable */
  jest.spyOn(require("../utils/AironeAPIClient"), "getUser").mockResolvedValue({
    json() {
      return Promise.resolve(user);
    },
  });
  /* eslint-enable */

  // wait async calls and get rendered fragment
  const result = render(<EditUserPasswordPage />, {
    wrapper: TestWrapper,
  });
  await waitForElementToBeRemoved(screen.getByTestId("loading"));

  expect(result).toMatchSnapshot();
});
