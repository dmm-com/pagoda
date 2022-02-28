/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";
import { BrowserRouter } from "react-router-dom";

import { EntryReferral } from "components/entry/EntryReferral";
import * as AironeAPIClient from "utils/AironeAPIClient";
import { TestWrapper } from "utils/TestWrapper";

afterEach(() => {
  jest.clearAllMocks();
});

test("should render a component with essential props", async () => {
  const entityId = 2;
  const entryId = 1;

  const referredEntries = {
    entries: [
      {
        id: 1,
        name: "name",
        entity: "entity",
      },
    ],
  };

  // tslint:disable-next-line:no-var-requires
  jest.spyOn(AironeAPIClient, "getReferredEntries").mockResolvedValue({
    json() {
      return Promise.resolve(referredEntries);
    },
  });

  expect(() =>
    render(
      <BrowserRouter>
        <EntryReferral entityId={entityId} entryId={entryId} />
      </BrowserRouter>,
      { wrapper: TestWrapper }
    )
  ).not.toThrow();
});
