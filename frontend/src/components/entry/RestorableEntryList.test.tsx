/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { RestorableEntryList } from "./RestorableEntryList";

import { TestWrapper } from "TestWrapper";

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
    render(<RestorableEntryList entityId={0} />, {
      wrapper: TestWrapper,
    })
  ).not.toThrow();
});
