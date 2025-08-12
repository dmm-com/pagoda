/**
 * @jest-environment jsdom
 */

import { Role } from "@dmm-com/airone-apiclient-typescript-fetch";
import { act, render, screen, waitFor, within } from "@testing-library/react";
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

  test("should show role list", async () => {
    /* eslint-disable */
    jest
      .spyOn(require("repository/AironeApiClient").aironeApiClient, "getRoles")
      .mockResolvedValue(Promise.resolve(roles));
    jest
      .spyOn(
        require("repository/AironeApiClient").aironeApiClient,
        "deleteRole",
      )
      .mockResolvedValue(Promise.resolve());
    /* eslint-enable */

    await act(async () => {
      render(<RoleList />, { wrapper: TestWrapper });
    });
    await waitFor(() => {
      expect(screen.queryByTestId("loading")).not.toBeInTheDocument();
    });

    // tr's in the tbody
    expect(
      within(screen.getAllByRole("rowgroup")[1]).getAllByRole("row"),
    ).toHaveLength(2);

    // delete first element
    await act(async () => {
      // now there is 2 elements, and each element has 2 buttons (delete, edit)
      // click the delete button of the first element
      screen.getAllByRole("button")[0].click();
    });
    await act(async () => {
      screen.getByRole("button", { name: "Yes" }).click();
    });

    await waitFor(() => {
      screen.getByText("ロールの削除が完了しました");
    });
  });
});
