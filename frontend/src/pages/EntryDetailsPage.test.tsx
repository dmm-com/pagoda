/**
 * @jest-environment jsdom
 */

import { render, screen, act, waitFor } from "@testing-library/react";
import React from "react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";

import { TestWrapperWithoutRoutes } from "TestWrapper";
import { EntryDetailsPage } from "pages/EntryDetailsPage";
import { entryDetailsPath } from "routes/Routes";

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

  const referredEntries = [
    {
      id: 1,
      name: "aaa",
      schema: {
        id: 2,
        name: "bbb",
      },
    },
  ];

  /* eslint-disable */
  jest
    .spyOn(
      require("repository/AironeApiClient").aironeApiClient,
      "getEntryReferral"
    )
    .mockResolvedValue(
      Promise.resolve({
        results: referredEntries,
        count: referredEntries.length,
      })
    );

  jest
    .spyOn(require("repository/AironeApiClient").aironeApiClient, "getEntry")
    .mockResolvedValue(Promise.resolve(entry));
  /* eslint-enable */

  const router = createMemoryRouter(
    [
      {
        path: entryDetailsPath(":entityId", ":entryId"),
        element: <EntryDetailsPage />,
      },
    ],
    {
      initialEntries: ["/ui/entities/2/entries/1/details"],
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
