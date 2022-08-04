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
import { EntryDetailsPage } from "pages/EntryDetailsPage";
import { TestWrapper } from "utils/TestWrapper";

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
      entity: "bbb",
    },
  ];

  /* eslint-disable */
  jest
    .spyOn(
      require("apiclient/AironeApiClientV2").aironeApiClientV2,
      "getEntryReferral"
    )
    .mockResolvedValue(
      Promise.resolve({
        results: referredEntries,
        count: referredEntries.length,
      })
    );

  jest
    .spyOn(require("apiclient/AironeApiClientV2").aironeApiClientV2, "getEntry")
    .mockResolvedValue(Promise.resolve(entry));
  /* eslint-enable */

  // wait async calls and get rendered fragment
  const result = render(
    <MemoryRouter initialEntries={["/new-ui/entities/2/entries/1/details"]}>
      <Route
        path={entryDetailsPath(":entityId", ":entryId")}
        component={EntryDetailsPage}
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
