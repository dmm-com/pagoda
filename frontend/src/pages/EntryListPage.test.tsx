/**
 * @jest-environment jsdom
 */

import { act, render, screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import React from "react";
import { createMemoryRouter, RouterProvider } from "react-router";

import { EntryListPage } from "./EntryListPage";

import { TestWrapperWithoutRoutes } from "TestWrapper";
import { entityEntriesPath } from "routes/Routes";

const server = setupServer(
  // getEntity
  http.get("http://localhost/entity/api/v2/1", () => {
    return HttpResponse.json({
      id: 1,
      name: "aaa",
      note: "",
      is_toplevel: false,
      attrs: [],
      webhooks: [],
    });
  }),
  // getEntries
  http.get("http://localhost/entity/api/v2/1/entries/", () => {
    return HttpResponse.json({
      count: 2,
      next: null,
      previous: null,
      results: [
        {
          id: 1,
          name: "aaa",
          schema: null,
          is_active: true,
          aliases: [],
        },
        {
          id: 2,
          name: "aaaaa",
          schema: null,
          is_active: true,
          aliases: [],
        },
        {
          id: 3,
          name: "bbbbb",
          schema: null,
          is_active: true,
          aliases: [],
        },
      ],
    });
  }),
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe("EntryListPage", () => {
  test("should match snapshot", async () => {
    const router = createMemoryRouter(
      [
        {
          path: entityEntriesPath(":entityId"),
          element: <EntryListPage />,
        },
      ],
      {
        initialEntries: ["/ui/entities/1/entries"],
      },
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
});
