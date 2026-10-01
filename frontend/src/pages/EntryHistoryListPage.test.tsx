/**
 */

import { render, screen, act, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import { createMemoryRouter, RouterProvider } from "react-router";

import { showEntryHistoryPath } from "../routes/Routes";

import { EntryHistoryListPage } from "./EntryHistoryListPage";

import { TestWrapperWithoutRoutes } from "TestWrapper";
import i18n from "i18n/config";

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
  // getEntryHistories
  http.get("http://localhost/entry/api/v2/1/histories/", () => {
    return HttpResponse.json({
      count: 0,
      results: [],
    });
  }),
  // getEntrySelfHistories (AironeApiClient uses relative fetch, not apiclient base URL)
  http.get("/entry/api/v2/1/self_histories/", () => {
    return HttpResponse.json({
      count: 0,
      results: [],
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
        path: showEntryHistoryPath(":entityId", ":entryId"),
        element: <EntryHistoryListPage />,
      },
    ],
    {
      initialEntries: [showEntryHistoryPath(2, 1)],
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

  vi.clearAllMocks();
});

test("renders in English", async () => {
  await act(async () => {
    await i18n.changeLanguage("en");
  });

  const router = createMemoryRouter(
    [
      {
        path: showEntryHistoryPath(":entityId", ":entryId"),
        element: <EntryHistoryListPage />,
      },
    ],
    {
      initialEntries: [showEntryHistoryPath(2, 1)],
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

  expect(screen.getAllByText("Change History").length).toBeGreaterThan(0);
  expect(screen.getByText("Entry change history")).toBeInTheDocument();
  expect(screen.getByText("Attribute change history")).toBeInTheDocument();

  vi.clearAllMocks();
});
