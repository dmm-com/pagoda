/**
 */

import {
  render,
  screen,
  act,
  fireEvent,
  waitFor,
} from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import { createMemoryRouter, RouterProvider } from "react-router";
import { vi } from "vitest";

import { TestWrapperWithoutRoutes } from "TestWrapper";
import { UserEditPage } from "pages/UserEditPage";
import { aironeApiClient } from "repository/AironeApiClient";

const server = setupServer(
  // getUser
  http.get("http://localhost/role/api/v2/roles/1", () => {
    return HttpResponse.json({
      id: 1,
      username: "user1",
      email: "user1@example.com",
      is_superuser: false,
    });
  }),
);

beforeAll(() => server.listen());

afterEach(() => server.resetHandlers());

afterAll(() => server.close());

describe("EditUserPage", () => {
  Object.defineProperty(window, "django_context", {
    value: {
      user: {
        id: 1,
        is_superuser: false,
      },
    },
    writable: false,
  });

  test("should match snapshot", async () => {
    const router = createMemoryRouter([
      {
        path: "/",
        element: <UserEditPage />,
      },
    ]);
    const result = await act(async () => {
      return render(<RouterProvider router={router} />, {
        wrapper: TestWrapperWithoutRoutes,
      });
    });
    await waitFor(() => {
      expect(screen.queryByTestId("loading")).not.toBeInTheDocument();
    });

    expect(result).toMatchSnapshot();
  });

  test("should allow saving a second change without leaving the edit page", async () => {
    const user = {
      id: 1,
      username: "user1",
      email: "user1@example.com",
      isSuperuser: false,
      dateJoined: "",
      parentUser: undefined,
      token: { value: "token", lifetime: 86400, expire: "", created: "" },
      authenticateType: 1,
      groups: [],
      roles: [],
    } as never;
    vi.spyOn(aironeApiClient, "getUser").mockResolvedValue(user);
    const updateUser = vi
      .spyOn(aironeApiClient, "updateUser")
      .mockResolvedValue({} as never);

    const router = createMemoryRouter(
      [{ path: "/users/:userId", element: <UserEditPage /> }],
      { initialEntries: ["/users/1"] },
    );
    render(<RouterProvider router={router} />, {
      wrapper: TestWrapperWithoutRoutes,
    });

    await waitFor(() => {
      expect(screen.queryByTestId("loading")).not.toBeInTheDocument();
    });

    const lifetime = screen
      .getByTestId("token-lifetime")
      .querySelector("input");
    expect(lifetime).not.toBeNull();
    fireEvent.change(lifetime!, { target: { value: "3600" } });
    fireEvent.blur(lifetime!);
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "保存" })).toBeEnabled(),
    );
    fireEvent.click(screen.getByRole("button", { name: "保存" }));

    await waitFor(() => expect(updateUser).toHaveBeenCalledTimes(1));
    expect(router.state.location.pathname).toBe("/users/1");

    fireEvent.change(lifetime!, { target: { value: "7200" } });
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "保存" })).toBeEnabled(),
    );
  });
});
