/**
 * @jest-environment jsdom
 */

import {
  render,
  waitForElementToBeRemoved,
  screen,
} from "@testing-library/react";
import React from "react";
import { AironeAPIClient } from "utils";

import { aironeApiClientV2 } from "apiclient/AironeApiClientV2";
import { EntryDetailsPage } from "pages/EntryDetailsPage";
import { TestWrapper } from "utils/TestWrapper";

afterEach(() => {
  jest.clearAllMocks();
});

test("should match snapshot", async () => {
  const entry = {
    id: 1,
    name: "aaa",
    schema: {
      id: 2,
      name: "bbb",
    },
    attrs: [],
  };

  const referredEntries = {
    entries: [
      {
        id: 1,
        name: "aaa",
        entity: "bbb",
      },
    ],
  };

  jest.spyOn(AironeAPIClient, "getReferredEntries").mockResolvedValue({
    json() {
      return Promise.resolve(referredEntries);
    },
  });

  jest
    .spyOn(aironeApiClientV2, "getGroups")
    .mockResolvedValue(Promise.resolve(entry));

  // wait async calls and get rendered fragment
  const result = render(<EntryDetailsPage />, {
    wrapper: TestWrapper,
  });
  await waitForElementToBeRemoved(screen.getByTestId("loading"));

  expect(result).toMatchSnapshot();
});
