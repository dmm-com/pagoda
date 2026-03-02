/**
 * @jest-environment jsdom
 */

import { PaginatedUserListList } from "@dmm-com/airone-apiclient-typescript-fetch";
import { act, render, screen } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router";

import { UserList } from "./UserList";

import { TestWrapper, TestWrapperWithoutRoutes } from "TestWrapper";
import { aironeApiClient } from "repository/AironeApiClient";
import { ServerContext } from "services/ServerContext";

// Mock ServerContext
jest.mock("services/ServerContext", () => ({
  ServerContext: {
    getInstance: jest.fn(),
  },
}));

// Mock API
jest.mock("repository/AironeApiClient", () => ({
  aironeApiClient: {
    getUsers: jest.fn(),
    destroyUser: jest.fn(),
  },
}));

afterEach(() => {
  jest.clearAllMocks();
});

describe("UserList", () => {
  const mockUsers: PaginatedUserListList = {
    count: 2,
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

  beforeEach(() => {
    (aironeApiClient.getUsers as jest.Mock).mockResolvedValue(mockUsers);
  });

  test("should render users", async () => {
    (ServerContext.getInstance as jest.Mock).mockReturnValue({
      user: { username: "user1", isSuperuser: false },
    });

    await act(async () => {
      render(<UserList />, { wrapper: TestWrapper });
    });

    expect(screen.getByText("user1")).toBeInTheDocument();
    expect(screen.getByText("user2")).toBeInTheDocument();
  });

  test("superuser sees menu for all users", async () => {
    (ServerContext.getInstance as jest.Mock).mockReturnValue({
      user: { username: "admin", isSuperuser: true },
    });

    await act(async () => {
      render(<UserList />, { wrapper: TestWrapper });
    });

    const menuIcons = screen.getAllByTestId("MoreVertIcon");
    expect(menuIcons.length).toBe(2);
  });

  test("normal user sees menu only for themselves", async () => {
    (ServerContext.getInstance as jest.Mock).mockReturnValue({
      user: { username: "user1", isSuperuser: false },
    });

    await act(async () => {
      render(<UserList />, { wrapper: TestWrapper });
    });

    const menuIcons = screen.getAllByTestId("MoreVertIcon");
    expect(menuIcons.length).toBe(1);
  });

  test("normal user cannot use register button", async () => {
    (ServerContext.getInstance as jest.Mock).mockReturnValue({
      user: { username: "user1", isSuperuser: false },
    });

    await act(async () => {
      render(<UserList />, { wrapper: TestWrapper });
    });

    const registerLink = screen.getByRole("link", {
      name: /新規ユーザを登録/i,
    });
    expect(registerLink.classList.contains("Mui-disabled")).toBe(true);
  });

  test("superuser can use register button", async () => {
    (ServerContext.getInstance as jest.Mock).mockReturnValue({
      user: { username: "admin", isSuperuser: true },
    });

    await act(async () => {
      render(<UserList />, { wrapper: TestWrapper });
    });

    const registerLink = screen.getByRole("link", {
      name: /新規ユーザを登録/i,
    });
    expect(registerLink.classList.contains("Mui-disabled")).toBe(false);
  });

  test("should navigate to create page", async () => {
    (ServerContext.getInstance as jest.Mock).mockReturnValue({
      user: { username: "admin", isSuperuser: true },
    });

    const router = createMemoryRouter([
      {
        path: "/",
        element: <UserList />,
      },
    ]);

    await act(async () => {
      render(<RouterProvider router={router} />, {
        wrapper: TestWrapperWithoutRoutes,
      });
    });

    await act(async () => {
      screen.getByRole("link", { name: /新規ユーザを登録/i }).click();
    });

    expect(router.state.location.pathname).toBe("/ui/users/new");
  });

  test("should navigate to user detail page", async () => {
    (ServerContext.getInstance as jest.Mock).mockReturnValue({
      user: { username: "admin", isSuperuser: true },
    });

    const router = createMemoryRouter([
      {
        path: "/",
        element: <UserList />,
      },
    ]);

    await act(async () => {
      render(<RouterProvider router={router} />, {
        wrapper: TestWrapperWithoutRoutes,
      });
    });

    await act(async () => {
      screen.getByRole("link", { name: "user1" }).click();
    });

    expect(router.state.location.pathname).toBe("/ui/users/1");
  });
});
