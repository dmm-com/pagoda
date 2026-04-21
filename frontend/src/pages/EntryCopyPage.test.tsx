/**
 * @jest-environment jsdom
 */

import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import { createMemoryRouter, RouterProvider } from "react-router";

import { EntryCopyPage } from "./EntryCopyPage";

import { TestWrapperWithoutRoutes } from "TestWrapper";
import { aironeApiClient } from "repository/AironeApiClient";
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
      isolation_rules: [],
      delete_chain_exclude_entities: [],
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

test("should show info variant snackbar on successful copy submission", async () => {
  jest
    .spyOn(aironeApiClient, "copyEntry")
    .mockResolvedValue(
      {} as ReturnType<typeof aironeApiClient.copyEntry> extends Promise<
        infer T
      >
        ? T
        : never,
    );

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

  await act(async () => {
    render(<RouterProvider router={router} />, {
      wrapper: TestWrapperWithoutRoutes,
    });
  });
  await waitFor(() => {
    expect(screen.queryByTestId("loading")).not.toBeInTheDocument();
  });

  // Enter copy target names in the textarea
  const textarea = screen.getByPlaceholderText("コピーするアイテム名");
  fireEvent.change(textarea, { target: { value: "copy-entry-1" } });

  // Click the copy button
  const copyButton = screen.getByRole("button", { name: "コピーを作成" });
  fireEvent.click(copyButton);

  await waitFor(() => {
    expect(
      screen.getByText("コピーのジョブ登録に成功しました"),
    ).toBeInTheDocument();
  });
});
