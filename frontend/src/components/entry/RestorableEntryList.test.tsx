/**
 */

import { act, render, screen } from "@testing-library/react";

import { RestorableEntryList } from "./RestorableEntryList";

import { TestWrapper } from "TestWrapper";
import { aironeApiClient } from "repository/AironeApiClient";

afterEach(() => {
  vi.clearAllMocks();
});

test("should render a component with essential props", async () => {
  vi.spyOn(aironeApiClient, "getEntries").mockResolvedValue(
    Promise.resolve({
      count: 0,
      results: [],
    }),
  );

  await act(async () => {
    render(<RestorableEntryList entityId={0} />, {
      wrapper: TestWrapper,
    });
  });

  expect(screen.getByText("0 - 0 / 0 件")).toBeInTheDocument();
});
