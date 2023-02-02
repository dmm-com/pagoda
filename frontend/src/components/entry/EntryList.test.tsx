/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { EntryList } from "components/entry/EntryList";
import { TestWrapper } from "services/TestWrapper";

afterEach(() => {
  jest.clearAllMocks();
});

test("should render a component with essential props", function () {
  /* eslint-disable */
  jest
    .spyOn(
      require("apiclient/AironeApiClientV2").aironeApiClientV2,
      "getEntries"
    )
    .mockResolvedValue(
      Promise.resolve({
        count: 0,
        results: [],
      })
    );
  /* eslint-enable */

  expect(() =>
    render(<EntryList entityId={0} />, {
      wrapper: TestWrapper,
    })
  ).not.toThrow();
});
