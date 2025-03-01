/**
 * @jest-environment jsdom
 */

import { act, render, screen, waitFor } from "@testing-library/react";
import React from "react";
import { createMemoryRouter, RouterProvider } from "react-router";

import { TestWrapperWithoutRoutes } from "TestWrapper";
import { EntryReferral } from "components/entry/EntryReferral";

afterEach(() => {
  jest.clearAllMocks();
});

test("should render a component with essential props", async () => {
  const entryId = 1;

  const referredEntries = [
    {
      id: 1,
      name: "entry1",
      schema: {
        id: 2,
        name: "entity1",
      },
    },
  ];

  /* eslint-disable */
  jest
    .spyOn(
      require("repository/AironeApiClient").aironeApiClient,
      "getEntryReferral",
    )
    .mockResolvedValue(
      Promise.resolve({
        results: referredEntries,
        count: referredEntries.length,
      }),
    );
  /* eslint-enable */

  const router = createMemoryRouter([
    {
      path: "/",
      element: <EntryReferral entryId={entryId} />,
    },
  ]);
  await act(async () => {
    return render(<RouterProvider router={router} />, {
      wrapper: TestWrapperWithoutRoutes,
    });
  });
  await waitFor(() => {
    expect(screen.queryByTestId("loading")).not.toBeInTheDocument();
  });

  expect(screen.getByText("entry1")).toBeInTheDocument();

  jest.clearAllMocks();
});
