/**
 * @jest-environment jsdom
 */

import { render, screen, act, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import React from "react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";

import { EntryRestorePage } from "./EntryRestorePage";

import { TestWrapperWithoutRoutes } from "TestWrapper";
import { restoreEntryPath } from "routes/Routes";

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
      count: 3,
      next: null,
      previous: null,
      results: [
        {
          id: 1,
          name: "aaa",
          schema: null,
          is_active: true,
        },
        {
          id: 2,
          name: "aaaaa",
          schema: null,
          is_active: true,
        },
        {
          id: 3,
          name: "bbbbb",
          schema: null,
          is_active: true,
        },
      ],
    });
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

test("should match snapshot", async () => {
  const router = createMemoryRouter(
    [
      {
        path: restoreEntryPath(":entityId"),
        element: <EntryRestorePage />,
      },
    ],
    {
      initialEntries: [restoreEntryPath(1)],
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
