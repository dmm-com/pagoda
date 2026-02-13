/**
 * @jest-environment jsdom
 */

import { act, render, screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import { createMemoryRouter, RouterProvider } from "react-router";

import { EntryCopyPage } from "./EntryCopyPage";

import { TestWrapperWithoutRoutes } from "TestWrapper";
import { copyEntryPath } from "routes/Routes";

const server = setupServer(
  // getEntity
  http.get("http://localhost/entity/api/v2/2/", () => {
    return HttpResponse.json({
      id: 2,
      name: "test entity",
      item_name_type: "US",
      is_toplevel: true,
      attrs: [],
      webhooks: [],
      hasOngoingChanges: false,
      permission: 3,
    });
  }),

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
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

test("should match snapshot", async () => {
  const router = createMemoryRouter(
    [
      {
        path: copyEntryPath(":entityId", ":entryId"),
        element: <EntryCopyPage />,
      },
    ],
    {
      initialEntries: [copyEntryPath(2, 1)],
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
