/**
 */

import { act, render, screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import { createMemoryRouter, RouterProvider } from "react-router";

import { RoleEditPage } from "./RoleEditPage";

import { TestWrapperWithoutRoutes } from "TestWrapper";
import i18n from "i18n/config";
import { aironeApiClient } from "repository/AironeApiClient";

const server = setupServer(
  // getRole
  http.get("http://localhost/role/api/v2/roles/1", () => {
    return HttpResponse.json({
      id: 1,
      name: "role1",
      description: "role1",
      users: [],
      groups: [],
      admin_users: [],
      admin_groups: [],
      is_editable: true,
    });
  }),
  // getGroups
  http.get("http://localhost/group/api/v2/groups", () => {
    return HttpResponse.json({
      count: 2,
      next: null,
      previous: null,
      results: [
        {
          id: 1,
          name: "group1",
          members: [
            {
              id: 1,
              username: "user1",
            },
          ],
          parent_group: null,
        },
        {
          id: 2,
          name: "group2",
          members: [
            {
              id: 2,
              username: "user2",
            },
          ],
          parent_group: 1,
        },
      ],
    });
  }),
  // getUsers
  http.get("http://localhost/user/api/v2/", () => {
    return HttpResponse.json({
      count: 2,
      next: null,
      previous: null,
      results: [
        {
          id: 1,
          username: "user1",
          email: "user1@example.com",
          is_superuser: false,
        },
        {
          id: 2,
          username: "user2",
          email: "user2@example.com",
          is_superuser: false,
        },
      ],
    });
  }),
);

beforeAll(() => server.listen());

afterEach(() => server.resetHandlers());

afterAll(() => server.close());

describe("EditRolePage", () => {
  test("should match snapshot", async () => {
    const router = createMemoryRouter([
      {
        path: "/",
        element: <RoleEditPage />,
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

  test("renders in English", async () => {
    await act(async () => {
      await i18n.changeLanguage("en");
    });

    const router = createMemoryRouter([
      {
        path: "/",
        element: <RoleEditPage />,
      },
    ]);
    await act(async () => {
      render(<RouterProvider router={router} />, {
        wrapper: TestWrapperWithoutRoutes,
      });
    });
    await waitFor(() => {
      expect(screen.queryByTestId("loading")).not.toBeInTheDocument();
    });

    expect(screen.getAllByText("Edit role").length).toBeGreaterThan(0);
  });
});

test("links an existing role to its change history", async () => {
  const getRole = vi.spyOn(aironeApiClient, "getRole").mockResolvedValue({
    id: 3,
    name: "role3",
    description: "",
    isEditable: true,
    users: [],
    groups: [],
    adminUsers: [],
    adminGroups: [],
    permissions: [],
  });
  try {
    const router = createMemoryRouter(
      [{ path: "/ui/roles/:roleId", element: <RoleEditPage /> }],
      { initialEntries: ["/ui/roles/3"] },
    );
    render(<RouterProvider router={router} />, {
      wrapper: TestWrapperWithoutRoutes,
    });
    expect(
      await screen.findByRole("link", { name: i18n.t("role.history.title") }),
    ).toHaveAttribute("href", "/ui/roles/3/history");
  } finally {
    getRole.mockRestore();
  }
});
