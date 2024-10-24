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
import { createMemoryHistory } from "history";
import React from "react";
import { Router } from "react-router-dom";

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

  test("should navigate to user create page", async () => {
    const history = createMemoryHistory();

    await act(async () => {
      render(
        <Router history={history}>
          <UserList />
        </Router>,
        { wrapper: TestWrapperWithoutRoutes }
      );
    });

    await waitFor(() => {
      expect(screen.queryByTestId("loading")).not.toBeInTheDocument();
    });

    await act(async () => {
      screen.getByRole("link", { name: "新規ユーザを登録" }).click();
    });

    expect(history.location.pathname).toBe("/ui/users/new");
  });

  test("should navigate to user details page", async function () {
    const history = createMemoryHistory();

    await act(async () => {
      render(
        <Router history={history}>
          <UserList />
        </Router>,
        { wrapper: TestWrapperWithoutRoutes }
      );
    });

    await waitFor(() => {
      expect(screen.queryByTestId("loading")).not.toBeInTheDocument();
    });

    await act(async () => {
      screen.getByRole("link", { name: "user1" }).click();
    });

    expect(history.location.pathname).toBe("/ui/users/1");
  });

  test("should delete a user", async function () {
    await act(async () => {
      render(<UserList />, { wrapper: TestWrapper });
    });

    await waitFor(() => {
      expect(screen.queryByTestId("loading")).not.toBeInTheDocument();
    });

    await act(async () => {
      // open a menu for user1
      // NOTE there are 4 buttons (user1 copy, user1 menu, user2 copy, user2 menu)
      screen.getAllByRole("button")[1].click();
    });
    await act(async () => {
      screen.getByRole("menuitem", { name: "削除" }).click();
    });
    await act(async () => {
      screen.getByRole("button", { name: "Yes" }).click();
    });

    await waitFor(() => {
      screen.getByText("ユーザ(user1)の削除が完了しました");
    });
  });
});
