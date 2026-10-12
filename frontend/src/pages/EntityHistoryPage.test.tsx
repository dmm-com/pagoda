/**
 */

import { act, render, screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import { createMemoryRouter, RouterProvider } from "react-router";

import { TestWrapperWithoutRoutes } from "TestWrapper";
import i18n from "i18n/config";
import { EntityHistoryPage } from "pages/EntityHistoryPage";
import { entityHistoryPath } from "routes/Routes";

const entity = {
  id: 1,
  name: "aaa",
  note: "",
  is_toplevel: false,
  has_ongoing_changes: false,
  attrs: [],
  webhooks: [],
  isolation_rules: [],
  delete_chain_exclude_entities: [],
};
const histories = {
  count: 2,
  results: [
    {
      operation: 1,
      time: new Date(2022, 0, 1, 0, 0, 0),
      username: "aaa",
      target_obj: "aaa",
      text: "text",
      is_detail: false,
      changes: [],
    },
    {
      operation: 1,
      time: new Date(2022, 0, 1, 0, 0, 0),
      username: "bbb",
      target_obj: "bbb",
      text: "text",
      is_detail: false,
      changes: [],
    },
  ],
};

const server = setupServer(
  // getEntityHistories
  http.get("http://localhost/entity/api/v2/1/histories", () => {
    return HttpResponse.json(histories);
  }),
  // getEntity
  http.get("http://localhost/entity/api/v2/1/", () => {
    return HttpResponse.json(entity);
  }),
);

beforeAll(() => server.listen());

afterEach(() => server.resetHandlers());

afterAll(() => server.close());

test("should match snapshot", async () => {
  const router = createMemoryRouter(
    [
      {
        path: entityHistoryPath(":entityId"),
        element: <EntityHistoryPage />,
      },
    ],
    {
      initialEntries: [entityHistoryPath(1)],
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

test("should render change history header in English", async () => {
  await act(async () => {
    await i18n.changeLanguage("en");
  });

  const router = createMemoryRouter(
    [
      {
        path: entityHistoryPath(":entityId"),
        element: <EntityHistoryPage />,
      },
    ],
    {
      initialEntries: [entityHistoryPath(1)],
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

  expect(screen.getAllByText("Change history").length).toBeGreaterThan(0);
});
