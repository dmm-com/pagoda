/**
 * @jest-environment jsdom
 */

import { render, screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import React from "react";

import { TestWrapper } from "TestWrapper";
import { UserListPage } from "pages/UserListPage";

const server = setupServer(
  // getUsers
  http.get("http://localhost/user/api/v2/", () => {
    return HttpResponse.json({
      count: 1,
      next: null,
      previous: null,
      results: [
        {
          id: 1,
          username: "user1",
          email: "user1@example.com",
          is_superuser: false,
        },
      ],
    });
  }),
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe("UserListPage", () => {
  test("should match snapshot", async () => {
    Object.defineProperty(window, "django_context", {
      value: {
        user: {
          is_superuser: false,
        },
      },
      writable: false,
    });

    const result = render(<UserListPage />, {
      wrapper: TestWrapper,
    });
    await waitFor(() => {
      expect(screen.queryByTestId("loading")).not.toBeInTheDocument();
    });

    expect(result).toMatchSnapshot();
  });
});
