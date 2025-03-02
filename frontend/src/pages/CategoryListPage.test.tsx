/**
 * @jest-environment jsdom
 */

import { render, screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import React from "react";
import { createMemoryRouter, RouterProvider } from "react-router";

import { TestWrapperWithoutRoutes } from "TestWrapper";
import { CategoryListPage } from "pages/CategoryListPage";
import { listCategoryPath } from "routes/Routes";

const server = setupServer(
  // GET /category/api/v2/
  http.get("http://localhost/category/api/v2/", () => {
    return HttpResponse.json({
      count: 2,
      next: null,
      previous: null,
      results: [
        {
          id: 1,
          name: "category1",
          note: "Sample Category 1",
          priority: 1,
          models: [
            { id: 1, name: "Entity1", is_public: true },
            { id: 2, name: "Entity2", is_public: true },
          ],
        },
        {
          id: 2,
          name: "category2",
          note: "Sample Category 2",
          priority: 2,
          models: [{ id: 3, name: "Entity3", is_public: true }],
        },
      ],
    });
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe("CategoryListPage", () => {
  it("renders the category list", async () => {
    // Create memory router
    const router = createMemoryRouter(
      [
        {
          path: listCategoryPath(),
          element: <CategoryListPage />,
        },
      ],
      {
        initialEntries: [listCategoryPath()],
      }
    );

    // Render component
    render(
      <TestWrapperWithoutRoutes>
        <RouterProvider router={router} />
      </TestWrapperWithoutRoutes>
    );

    // Verify that the category list title is displayed (with specific element)
    expect(
      screen.getByRole("heading", { name: "カテゴリ一覧" })
    ).toBeInTheDocument();

    // Wait for categories to be displayed
    await waitFor(() => {
      expect(screen.getByText("category1")).toBeInTheDocument();
      expect(screen.getByText("category2")).toBeInTheDocument();
    });
  });
});
