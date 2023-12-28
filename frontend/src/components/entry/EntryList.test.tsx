/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { TestWrapper } from "TestWrapper";
import { EntryList } from "components/entry/EntryList";

afterEach(() => {
  jest.clearAllMocks();
});

test("should render a component with essential props", function () {
  /* eslint-disable */
  jest
    .spyOn(
      require("repository/AironeApiClientV2").aironeApiClientV2,
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
