/**
 * @jest-environment jsdom
 */

import { Role } from "@dmm-com/airone-apiclient-typescript-fetch";
import {
  act,
  render,
  screen,
  waitForElementToBeRemoved,
  within,
} from "@testing-library/react";
import React from "react";

import { RoleList } from "./RoleList";

import { TestWrapper } from "TestWrapper";

afterEach(() => {
  jest.clearAllMocks();
});

describe("RoleList", () => {
  const roles: Role[] = [
    {
      id: 1,
      name: "role1",
      description: "role1",
      users: [],
      groups: [],
      adminUsers: [],
      adminGroups: [],
      isEditable: true,
    },
    {
      id: 2,
      name: "role2",
      description: "role2",
      users: [],
      groups: [],
      adminUsers: [],
      adminGroups: [],
      isEditable: true,
    },
  ];

  test("should show role list", async function () {
    /* eslint-disable */
    jest
      .spyOn(
        require("repository/AironeApiClientV2").aironeApiClientV2,
        "getRoles"
      )
      .mockResolvedValue(Promise.resolve(roles));
    jest
      .spyOn(
        require("repository/AironeApiClientV2").aironeApiClientV2,
        "deleteRole"
      )
      .mockResolvedValue(Promise.resolve());
    /* eslint-enable */

    render(<RoleList />, { wrapper: TestWrapper });
    await waitForElementToBeRemoved(screen.getByTestId("loading"));

    // tr's in the tbody
    expect(
      within(screen.getAllByRole("rowgroup")[1]).getAllByRole("row")
    ).toHaveLength(2);

    // delete first element
    act(() => {
      // now there is 2 elements, and each element has 2 buttons (delete, edit)
      // click the delete button of the first element
      screen.getAllByRole("button")[0].click();
    });
    act(() => {
      screen.getByRole("button", { name: "Yes" }).click();
    });

    // TODO check if the deletion is successful
  });
});
