/**
 * @jest-environment jsdom
 */

import {
  render,
  waitForElementToBeRemoved,
  screen,
} from "@testing-library/react";
import React from "react";

import { AdvancedSearchResultValue } from "@dmm-com/airone-apiclient-typescript-fetch";
import { TestWrapper } from "TestWrapper";
import { AdvancedSearchResultsPage } from "pages/AdvancedSearchResultsPage";

afterEach(() => {
  jest.clearAllMocks();
});

test("should match snapshot", async () => {
  Object.defineProperty(window, "django_context", {
    value: {
      user: {
        is_superuser: false,
      },
    },
    writable: false,
  });

  const results: AdvancedSearchResultValue[] = [
    {
      entry: {
        id: 2,
        name: "entry1",
      },
      entity: {
        id: 1,
        name: "entity1",
      },
      attrs: {
        attr1: {
          type: 2,
          value: { asString: "attr1" },
          isReadable: true,
        },
        attr2: {
          type: 2,
          value: { asString: "attr1" },
          isReadable: true,
        },
      },
      isReadable: true,
    },
  ];

  /* eslint-disable */
  jest
    .spyOn(
      require("repository/AironeApiClientV2").aironeApiClientV2,
      "advancedSearch"
    )
    .mockResolvedValue(
      Promise.resolve({
        count: 1,
        values: results,
      })
    );
  jest
    .spyOn(
      require("repository/AironeApiClientV2").aironeApiClientV2,
      "getEntityAttrs"
    )
    .mockResolvedValue(Promise.resolve([]));
  /* eslint-enable */

  // wait async calls and get rendered fragment
  const result = render(<AdvancedSearchResultsPage />, {
    wrapper: TestWrapper,
  });
  await waitForElementToBeRemoved(screen.getByTestId("loading"));

  expect(result).toMatchSnapshot();
});
