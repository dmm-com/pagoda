/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";
import { BrowserRouter } from "react-router-dom";

import { EntryReferral } from "components/entry/EntryReferral";
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

  /* eslint-disable */
  jest
    .spyOn(require("utils/AironeAPIClient"), "getReferredEntries")
    .mockResolvedValue({
      json() {
        return Promise.resolve(referredEntries);
      },
    });
  /* eslint-enable */

  expect(() =>
    render(
      <BrowserRouter>
        <EntryReferral entityId={entityId} entryId={entryId} />
      </BrowserRouter>,
      { wrapper: TestWrapper }
    )
  ).not.toThrow();
});
