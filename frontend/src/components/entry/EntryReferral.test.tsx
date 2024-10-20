/**
 * @jest-environment jsdom
 */

import { act, render, screen } from "@testing-library/react";
import React from "react";
import { BrowserRouter } from "react-router-dom";

import { TestWrapper } from "TestWrapper";
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
      "getEntryReferral"
    )
    .mockResolvedValue(
      Promise.resolve({
        results: referredEntries,
        count: referredEntries.length,
      })
    );
  /* eslint-enable */

  await act(async () => {
    render(
      <BrowserRouter>
        <EntryReferral entryId={entryId} />
      </BrowserRouter>,
      { wrapper: TestWrapper }
    );
  });

  expect(screen.getByText("entry1")).toBeInTheDocument();

  jest.clearAllMocks();
});
