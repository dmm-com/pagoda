/**
 * @jest-environment jsdom
 */

import { render, screen, act, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import React from "react";
import { createMemoryRouter, RouterProvider } from "react-router";

import { TestWrapperWithoutRoutes } from "TestWrapper";
import { CategoryEditPage } from "pages/CategoryEditPage";
import { editCategoryPath } from "routes/Routes";

const server = setupServer(
  // getCategory
  http.get("http://localhost/category/api/v2/1", () => {
    return HttpResponse.json({
      id: 1,
      name: "category1",
      note: "サンプルカテゴリ",
      priority: 1,
      models: [
        { id: 1, name: "Entity1", is_public: true },
        { id: 2, name: "Entity2", is_public: true },
      ],
    });
  }),
  // getEntities
  http.get("http://localhost/entity/api/v2/", () => {
    return HttpResponse.json({
      count: 3,
      next: null,
      previous: null,
      results: [
        {
          id: 1,
          name: "Entity1",
          note: "",
          isToplevel: false,
          hasOngoingChanges: false,
          attrs: [],
          webhooks: [],
        },
        {
          id: 2,
          name: "Entity2",
          note: "",
          isToplevel: false,
          hasOngoingChanges: false,
          attrs: [],
          webhooks: [],
        },
        {
          id: 3,
          name: "Entity3",
          note: "",
          isToplevel: false,
          hasOngoingChanges: false,
          attrs: [],
          webhooks: [],
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
        path: editCategoryPath(":categoryId"),
        element: <CategoryEditPage />,
      },
    ],
    {
      initialEntries: [editCategoryPath(1)],
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
