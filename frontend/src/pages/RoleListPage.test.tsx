/**
 * @jest-environment jsdom
 */

import { Role } from "@dmm-com/airone-apiclient-typescript-fetch";
import {
  render,
  waitForElementToBeRemoved,
  screen,
} from "@testing-library/react";
import React from "react";

import { RoleListPage } from "./RoleListPage";

import { TestWrapper } from "TestWrapper";

afterEach(() => {
  jest.clearAllMocks();
});

test("should match snapshot", async () => {
  const roles: Role[] = [
    {
      id: 0,
      name: "",
      description: "",
      users: [],
      groups: [],
      adminUsers: [],
      adminGroups: [],
      isEditable: true,
    },
  ];

  /* eslint-disable */
  jest
    .spyOn(require("../repository/AironeApiClient").aironeApiClient, "getRoles")
    .mockResolvedValue(Promise.resolve(roles));
  /* eslint-enable */

  // wait async calls and get rendered fragment
  const result = render(<RoleListPage />, {
    wrapper: TestWrapper,
  });
  await waitForElementToBeRemoved(screen.getByTestId("loading"));

  expect(result).toMatchSnapshot();
});
