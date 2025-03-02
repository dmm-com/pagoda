/**
 * @jest-environment jsdom
 */

import { render, screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import React from "react";
import { createMemoryRouter, RouterProvider } from "react-router";

import { TestWrapperWithoutRoutes } from "TestWrapper";
import { AliasEntryListPage } from "pages/AliasEntryListPage";

// Setup mock location
const mockLocation = {
  pathname: "/ui/entities/1/alias",
  search: "",
  hash: "",
  state: null,
};

// Mock useLocation
jest.mock("react-use", () => ({
  ...jest.requireActual("react-use"),
  useLocation: () => mockLocation,
}));

const server = setupServer(
  // GET /entity/api/v2/:entityId/
  http.get("http://localhost/entity/api/v2/1/", () => {
    return HttpResponse.json({
      id: 1,
      name: "Entity1",
      note: "Test Entity",
      isToplevel: true,
      hasOngoingChanges: false,
      attrs: [],
      webhooks: [],
    });
  }),

  // GET /entry/api/v2/:entityId/
  http.get("http://localhost/entry/api/v2/1/", ({ request }) => {
    // Get query parameters (when isAlias is true)
    const url = new URL(request.url);
    const isAlias = url.searchParams.get("is_alias");

    if (isAlias === "true") {
      return HttpResponse.json({
        count: 2,
        next: null,
        previous: null,
        results: [
          {
            id: 1,
            name: "entry1",
            schema: 1,
            created_at: "2023-01-01T00:00:00Z",
            updated_at: "2023-01-01T00:00:00Z",
            created_user: { id: 1, username: "user1" },
            updated_user: { id: 1, username: "user1" },
            attrs: [],
            referrals: [],
            aliases: [],
            is_public: true,
            status: 0,
          },
          {
            id: 2,
            name: "entry2",
            schema: 1,
            created_at: "2023-01-02T00:00:00Z",
            updated_at: "2023-01-02T00:00:00Z",
            created_user: { id: 1, username: "user1" },
            updated_user: { id: 1, username: "user1" },
            attrs: [],
            referrals: [],
            aliases: [],
            is_public: true,
            status: 0,
          },
        ],
      });
    }

    return HttpResponse.json({
      count: 0,
      next: null,
      previous: null,
      results: [],
    });
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe("AliasEntryListPage", () => {
  it("renders the alias entry list", async () => {
    // Create memory router
    const router = createMemoryRouter(
      [
        {
          path: "/ui/entities/:entityId/alias",
          element: <AliasEntryListPage />,
        },
      ],
      {
        initialEntries: ["/ui/entities/1/alias"],
      }
    );

    // Render component
    render(
      <TestWrapperWithoutRoutes>
        <RouterProvider router={router} />
      </TestWrapperWithoutRoutes>
    );

    // Wait for page title to be displayed
    await waitFor(() => {
      const titleElement = screen.getByRole("heading", { name: "Entity1" });
      expect(titleElement).toBeInTheDocument();
    });
  });
});
