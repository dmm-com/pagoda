/**
 * @jest-environment jsdom
 */

import {
  render,
  waitForElementToBeRemoved,
  screen,
} from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import React from "react";

import { TestWrapper } from "TestWrapper";
import { EditUserPage } from "pages/EditUserPage";

const server = setupServer(
  // getUser
  http.get("http://localhost/role/api/v2/roles/1", () => {
    return HttpResponse.json({
      id: 1,
      username: "user1",
      email: "user1@example.com",
      is_superuser: false,
    });
  })
);

beforeAll(() => server.listen());

afterEach(() => server.resetHandlers());

afterAll(() => server.close());

describe("EditUserPage", () => {
  Object.defineProperty(window, "django_context", {
    value: {
      user: {
        is_superuser: false,
      },
    },
    writable: false,
  });

  test("should match snapshot", async () => {
    // wait async calls and get rendered fragment
    const result = render(<EditUserPage />, {
      wrapper: TestWrapper,
    });
    await waitForElementToBeRemoved(screen.getByTestId("loading"));

    expect(result).toMatchSnapshot();
  });
});
