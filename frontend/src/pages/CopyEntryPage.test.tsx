/**
 * @jest-environment jsdom
 */

import {
  render,
  waitForElementToBeRemoved,
  screen,
} from "@testing-library/react";
import React from "react";

import { CopyEntryPage } from "./CopyEntryPage";

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

  /* eslint-disable */
  jest
    .spyOn(require("apiclient/AironeApiClientV2").aironeApiClientV2, "getEntry")
    .mockResolvedValue(Promise.resolve(entry));
  /* eslint-enable */

  // wait async calls and get rendered fragment
  const result = render(<CopyEntryPage />, {
    wrapper: TestWrapper,
  });
  await waitForElementToBeRemoved(screen.getByTestId("loading"));

  expect(result).toMatchSnapshot();
});
