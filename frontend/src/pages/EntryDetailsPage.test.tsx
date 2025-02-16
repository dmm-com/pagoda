/**
 * @jest-environment jsdom
 */

import { act, render, screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import React from "react";
import { createMemoryRouter, RouterProvider } from "react-router";

import { TestWrapperWithoutRoutes } from "TestWrapper";
import { EntryDetailsPage } from "pages/EntryDetailsPage";
import { entryDetailsPath } from "routes/Routes";

const server = setupServer(
  // getEntry
  http.get("http://localhost/entry/api/v2/1/", () => {
    return HttpResponse.json({
      id: 1,
      name: "test entry",
      is_active: true,
      schema: {
        id: 2,
        name: "test entity",
      },
      attrs: [],
    });
  }),
  // getEntryReferral
  http.get("http://localhost/entry/api/v2/1/referral/", () => {
    return HttpResponse.json({
      count: 1,
      next: null,
      previous: null,
      results: [
        {
          id: 1,
          name: "aaa",
          schema: {
            id: 2,
            name: "bbb",
          },
          aliases: [],
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
        path: entryDetailsPath(":entityId", ":entryId"),
        element: <EntryDetailsPage />,
      },
    ],
    {
      initialEntries: [entryDetailsPath(2, 1)],
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

  jest.clearAllMocks();
});
