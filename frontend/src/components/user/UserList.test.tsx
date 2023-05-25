/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { TestWrapper } from "TestWrapper";
import { UserList } from "components/user/UserList";

afterEach(() => {
  jest.clearAllMocks();
});

test("should render a component with essential props", function () {
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
    .spyOn(
      require("repository/AironeApiClientV2").aironeApiClientV2,
      "getUsers"
    )
    .mockResolvedValue(Promise.resolve(users));
  /* eslint-enable */

  expect(() => render(<UserList />, { wrapper: TestWrapper })).not.toThrow();
});
