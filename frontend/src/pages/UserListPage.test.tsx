/**
 */

import { act, render, screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";

import { TestWrapper } from "TestWrapper";
import i18n from "i18n/config";
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

    let result: ReturnType<typeof render>;
    await act(async () => {
      result = render(<UserListPage />, {
        wrapper: TestWrapper,
      });
    });

    expect(result!).toMatchSnapshot();
  });

  test("renders in English", async () => {
    await act(async () => {
      await i18n.changeLanguage("en");
    });

    await act(async () => {
      render(<UserListPage />, {
        wrapper: TestWrapper,
      });
    });

    expect(screen.getAllByText("User management").length).toBeGreaterThan(0);
  });
});
