/**
 */

import { act, render, screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import { createMemoryRouter, RouterProvider } from "react-router";

import { EntryRestorePage } from "./EntryRestorePage";

import { TestWrapperWithoutRoutes } from "TestWrapper";
import i18n from "i18n/config";
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
      isolation_rules: [],
      delete_chain_exclude_entities: [],
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

test("renders in English", async () => {
  await act(async () => {
    await i18n.changeLanguage("en");
  });

  const router = createMemoryRouter(
    [
      {
        path: restoreEntryPath(":entityId"),
        element: <EntryRestorePage />,
      },
    ],
    {
      initialEntries: [restoreEntryPath(1)],
    },
  );
  await act(async () => {
    render(<RouterProvider router={router} />, {
      wrapper: TestWrapperWithoutRoutes,
    });
  });
  await waitFor(() => {
    expect(screen.queryByTestId("loading")).not.toBeInTheDocument();
  });

  expect(screen.getByText("Restore deleted entries")).toBeInTheDocument();
});
