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

import { RolePage } from "./RolePage";

import { TestWrapper } from "services/TestWrapper";

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
    },
  ];

  /* eslint-disable */
  jest
    .spyOn(
      require("../apiclient/AironeApiClientV2").aironeApiClientV2,
      "getRoles"
    )
    .mockResolvedValue(Promise.resolve(roles));
  /* eslint-enable */

  // wait async calls and get rendered fragment
  const result = render(<RolePage />, {
    wrapper: TestWrapper,
  });
  await waitForElementToBeRemoved(screen.getByTestId("loading"));

  expect(result).toMatchSnapshot();
});
