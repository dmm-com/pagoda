/**
 * @jest-environment jsdom
 */

import { render, screen, act, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import React from "react";
import { createMemoryRouter, RouterProvider } from "react-router";

import { TestWrapperWithoutRoutes } from "TestWrapper";
import { ListAliasEntryPage } from "pages/ListAliasEntryPage";
import { listAliasPath } from "routes/Routes";

// モックロケーションを設定
const mockLocation = {
  pathname: "/ui/entities/1/alias",
  search: "",
  hash: "",
  state: null,
};

// useLocationのモック
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
      note: "テストエンティティ",
      isToplevel: true,
      hasOngoingChanges: false,
      attrs: [],
      webhooks: [],
    });
  }),

  // GET /entry/api/v2/:entityId/
  http.get("http://localhost/entry/api/v2/1/", () => {
    return HttpResponse.json({
      count: 2,
      next: null,
      previous: null,
      results: [
        {
          id: 1,
          name: "Entry1",
          schema: 1,
          attrs: [],
          aliases: [
            { id: 101, name: "Alias1-1" },
            { id: 102, name: "Alias1-2" },
          ],
        },
        {
          id: 2,
          name: "Entry2",
          schema: 1,
          attrs: [],
          aliases: [{ id: 201, name: "Alias2-1" }],
        },
      ],
    });
  }),

  // GET /entity/api/v2/:entityId/entries/ の未処理リクエストに対するモック
  http.get("http://localhost/entity/api/v2/1/entries/", () => {
    return HttpResponse.json({
      count: 0,
      next: null,
      previous: null,
      results: [],
    });
  })
);

beforeAll(() => server.listen({ onUnhandledRequest: "warn" }));
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
        path: listAliasPath(":entityId"),
        element: <ListAliasEntryPage />,
      },
    ],
    {
      initialEntries: [listAliasPath(1)],
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
