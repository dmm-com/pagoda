/**
 * @jest-environment jsdom
 */

import {
  render,
  waitForElementToBeRemoved,
  screen,
} from "@testing-library/react";
import React from "react";

import { TestWrapper } from "../utils/TestWrapper";

import { AdvancedSearchResults } from "./AdvancedSearchResults";

afterEach(() => {
  jest.clearAllMocks();
});

test("should match snapshot", async () => {
  // TODO avoid to pass the global variable implicitly
  (window as any).django_context = {
    user: {
      is_superuser: false,
    },
  };

  const results = [
    {
      entry: {
        name: "entry1",
      },
      attrs: {
        attr1: {
          type: 1,
          value: "attr1",
        },
        attr2: {
          type: 1,
          value: "attr1",
        },
      },
    },
  ];

  /* eslint-disable */
  jest
    .spyOn(require("../utils/AironeAPIClient"), "searchEntries")
    .mockResolvedValue({
      json() {
        return Promise.resolve({
          result: {
            ret_values: results,
          },
        });
      },
    });
  /* eslint-enable */

  // wait async calls and get rendered fragment
  const result = render(<AdvancedSearchResults />, {
    wrapper: TestWrapper,
  });
  await waitForElementToBeRemoved(screen.getByTestId("loading"));

  expect(result).toMatchSnapshot();
});
