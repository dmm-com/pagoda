/**
 * @jest-environment jsdom
 */

import { render, screen, act, waitFor } from "@testing-library/react";
import React from "react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";

import { showEntryHistoryPath } from "../routes/Routes";

import { EntryHistoryListPage } from "./EntryHistoryListPage";

import { TestWrapperWithoutRoutes } from "TestWrapper";

afterEach(() => {
  jest.clearAllMocks();
});

test("should match snapshot", async () => {
  const entry = {
    id: 1,
    name: "aaa",
    isActive: true,
    schema: {
      id: 2,
      name: "bbb",
    },
    attrs: [],
  };

  const histories = {
    count: 0,
    results: [],
  };

  /* eslint-disable */
  jest
    .spyOn(require("repository/AironeApiClient").aironeApiClient, "getEntry")
    .mockResolvedValue(Promise.resolve(entry));

  jest
    .spyOn(
      require("repository/AironeApiClient").aironeApiClient,
      "getEntryHistories"
    )
    .mockResolvedValue(Promise.resolve(histories));
  /* eslint-enable */

  const router = createMemoryRouter(
    [
      {
        path: showEntryHistoryPath(":entityId", ":entryId"),
        element: <EntryHistoryListPage />,
      },
    ],
    {
      initialEntries: [showEntryHistoryPath(2, 1)],
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
