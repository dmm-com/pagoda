/**
 * @jest-environment jsdom
 */

import { render, screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import React from "react";

import { RoleListPage } from "./RoleListPage";

import { TestWrapper } from "TestWrapper";

const server = setupServer(
  // getRoles
  http.get("http://localhost/role/api/v2/", () => {
    return HttpResponse.json([
      {
        id: 1,
        name: "role1",
        description: "role1",
        users: [],
        groups: [],
        admin_users: [],
        admin_groups: [],
        is_editable: true,
      },
    ]);
  })
);

beforeAll(() => server.listen());

afterEach(() => server.resetHandlers());

afterAll(() => server.close());

describe("RoleListPage", () => {
  test("should match snapshot", async () => {
    // wait async calls and get rendered fragment
    const result = render(<RoleListPage />, {
      wrapper: TestWrapper,
    });
    await waitFor(() => {
      expect(screen.queryByTestId("loading")).not.toBeInTheDocument();
    });

    expect(result).toMatchSnapshot();
  });
});
