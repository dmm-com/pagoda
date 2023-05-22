/**
 * @jest-environment jsdom
 */

import {
  render,
  waitForElementToBeRemoved,
  screen,
} from "@testing-library/react";
import React from "react";

import { DashboardPage } from "./DashboardPage";

import { TestWrapper } from "TestWrapper";

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

  const entities = [
    {
      id: 1,
      name: "aaa",
      note: "",
      isToplevel: false,
      status: 1,
    },
    {
      id: 2,
      name: "aaaaa",
      note: "",
      isToplevel: false,
      status: 1,
    },
    {
      id: 3,
      name: "bbbbb",
      note: "",
      isToplevel: false,
      status: 1,
    },
  ];

  /* eslint-disable */
  jest
    .spyOn(
      require("../repository/AironeApiClientV2").aironeApiClientV2,
      "getEntities"
    )
    .mockResolvedValue(Promise.resolve({ results: entities }));
  /* eslint-enable */

  // wait async calls and get rendered fragment
  const result = render(<DashboardPage />, {
    wrapper: TestWrapper,
  });
  await waitForElementToBeRemoved(screen.getByTestId("loading"));

  expect(result).toMatchSnapshot();
});
