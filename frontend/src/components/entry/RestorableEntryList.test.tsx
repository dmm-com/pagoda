/**
 * @jest-environment jsdom
 */

import { act, render, screen } from "@testing-library/react";
import React from "react";

import { RestorableEntryList } from "./RestorableEntryList";

import { TestWrapper } from "TestWrapper";

afterEach(() => {
  jest.clearAllMocks();
});

test("should render a component with essential props", async () => {
  /* eslint-disable */
  jest
    .spyOn(require("repository/AironeApiClient").aironeApiClient, "getEntries")
    .mockResolvedValue(
      Promise.resolve({
        count: 0,
        results: [],
      })
    );
  /* eslint-enable */

  await act(async () => {
    render(<RestorableEntryList entityId={0} />, {
      wrapper: TestWrapper,
    });
  });

  expect(screen.getByText("0 - 0 / 0 件")).toBeInTheDocument();
});
