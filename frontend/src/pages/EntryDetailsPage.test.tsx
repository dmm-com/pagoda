/**
 * @jest-environment jsdom
 */

import {
  render,
  waitForElementToBeRemoved,
  screen,
} from "@testing-library/react";
import React from "react";
import { MemoryRouter, Route } from "react-router-dom";

import { entryDetailsPath } from "Routes";
import { TestWrapper } from "TestWrapper";
import { EntryDetailsPage } from "pages/EntryDetailsPage";

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

  // wait async calls and get rendered fragment
  const result = render(
    <MemoryRouter initialEntries={["/ui/entities/2/entries/1/details"]}>
      <Route
        path={entryDetailsPath(":entityId", ":entryId")}
        element={<EntryDetailsPage />}
      />
    </MemoryRouter>,
    {
      wrapper: TestWrapper,
    }
  );
  await waitForElementToBeRemoved(screen.getByTestId("loading"));

  expect(result).toMatchSnapshot();

  jest.clearAllMocks();
});
