/**
 * @jest-environment jsdom
 */

import { PaginatedUserListList } from "@dmm-com/airone-apiclient-typescript-fetch";
import {
  act,
  render,
  screen,
  waitFor,
  waitForElementToBeRemoved,
} from "@testing-library/react";
import React from "react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";

import { TestWrapper, TestWrapperWithoutRoutes } from "TestWrapper";
import { UserList } from "components/user/UserList";

afterEach(() => {
  jest.clearAllMocks();
});

describe("UserList", () => {
  const users: PaginatedUserListList = {
    count: 1,
    next: null,
    previous: null,
    results: [
      {
        id: 1,
        username: "user1",
        email: "user1@example.com",
        isSuperuser: false,
        dateJoined: "2020-01-01T00:00:00Z",
      },
      {
        id: 2,
        username: "user2",
        email: "user2@example.com",
        isSuperuser: false,
        dateJoined: "2020-02-01T00:00:00Z",
      },
    ],
  };

  /* eslint-disable */
  jest
    .spyOn(require("repository/AironeApiClient").aironeApiClient, "getUsers")
    .mockResolvedValue(Promise.resolve(users));
  jest
    .spyOn(require("repository/AironeApiClient").aironeApiClient, "destroyUser")
    .mockResolvedValue(Promise.resolve());
  /* eslint-enable */

  test("should show users", async function () {
    render(<UserList />, { wrapper: TestWrapper });

    await waitForElementToBeRemoved(screen.getByTestId("loading"));

    expect(screen.getAllByRole("link", { name: /user*/i })).toHaveLength(2);
  });

  test("should navigate to user create page", async function () {
    const router = createMemoryRouter([
      {
        path: "/",
        element: <UserList />,
      },
    ]);

    render(<RouterProvider router={router} />, {
      wrapper: TestWrapperWithoutRoutes,
    });

    await waitForElementToBeRemoved(screen.getByTestId("loading"));

    act(() => {
      screen.getByRole("link", { name: "新規ユーザを登録" }).click();
    });

    expect(router.state.location.pathname).toBe("/ui/users/new");
  });

  test("should navigate to user details page", async function () {
    const router = createMemoryRouter([
      {
        path: "/",
        element: <UserList />,
      },
    ]);

    render(<RouterProvider router={router} />, {
      wrapper: TestWrapperWithoutRoutes,
    });

    await waitForElementToBeRemoved(screen.getByTestId("loading"));

    act(() => {
      screen.getByRole("link", { name: "user1" }).click();
    });

    expect(router.state.location.pathname).toBe("/ui/users/1");
  });

  test("should delete a user", async function () {
    render(<UserList />, { wrapper: TestWrapper });

    await waitForElementToBeRemoved(screen.getByTestId("loading"));

    act(() => {
      // open a menu for user1
      // NOTE there are 4 buttons (user1 copy, user1 menu, user2 copy, user2 menu)
      screen.getAllByRole("button")[1].click();
    });
    act(() => {
      screen.getByRole("menuitem", { name: "削除" }).click();
    });
    act(() => {
      screen.getByRole("button", { name: "Yes" }).click();
    });

    await waitFor(() => {
      screen.getByText("ユーザ(user1)の削除が完了しました");
    });
  });
});
