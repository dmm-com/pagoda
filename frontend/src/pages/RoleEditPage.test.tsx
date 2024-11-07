/**
 * @jest-environment jsdom
 */

import { act, render, screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import React from "react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";

import { RoleEditPage } from "./RoleEditPage";

import { TestWrapperWithoutRoutes } from "TestWrapper";

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
  })
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
});
