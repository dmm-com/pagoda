/**
 * @jest-environment jsdom
 */

import { render, screen, act, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import React from "react";
import { createMemoryRouter, RouterProvider } from "react-router";

import { TestWrapperWithoutRoutes } from "TestWrapper";
import { ListCategoryPage } from "pages/ListCategoryPage";
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
          note: "サンプルカテゴリ1",
          priority: 1,
          models: [
            { id: 1, name: "Entity1", is_public: true },
            { id: 2, name: "Entity2", is_public: true },
          ],
        },
        {
          id: 2,
          name: "category2",
          note: "サンプルカテゴリ2",
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

test("should match snapshot", async () => {
  Object.defineProperty(window, "django_context", {
    value: {
      user: {
        is_superuser: false,
      },
    },
    writable: false,
  });

  const router = createMemoryRouter(
    [
      {
        path: listCategoryPath(),
        element: <ListCategoryPage />,
      },
    ],
    {
      initialEntries: [listCategoryPath()],
    }
  );
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
