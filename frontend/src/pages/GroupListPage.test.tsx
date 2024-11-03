/**
 * @jest-environment jsdom
 */

import { render, screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import React from "react";

import { TestWrapper } from "TestWrapper";
import { GroupListPage } from "pages/GroupListPage";

const server = setupServer(
  // getGroupTrees
  http.get("http://localhost/group/api/v2/groups/tree", () => {
    return HttpResponse.json([
      {
        id: 1,
        name: "group1",
        children: [
          {
            id: 1,
            name: "group1",
            children: [],
          },
          {
            id: 2,
            name: "group2",
            children: [],
          },
        ],
      },
      {
        id: 2,
        name: "group2",
        children: [],
      },
    ]);
  })
);

beforeAll(() => server.listen());

afterEach(() => server.resetHandlers());

afterAll(() => server.close());

describe("GroupListPage", () => {
  test("should match snapshot", async () => {
    Object.defineProperty(window, "django_context", {
      value: {
        user: {
          isSuperuser: true,
        },
      },
      writable: false,
    });

    const result = render(<GroupListPage />, {
      wrapper: TestWrapper,
    });
    await waitFor(() => {
      expect(screen.queryByTestId("loading")).not.toBeInTheDocument();
    });

    expect(result).toMatchSnapshot();
  });
});
