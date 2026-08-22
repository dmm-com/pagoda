/**
 */

import { render } from "@testing-library/react";

import { UnavailableErrorPage } from "./UnavailableErrorPage";

import { TestWrapper } from "TestWrapper";

afterEach(() => {
  vi.clearAllMocks();
});

test("should match snapshot", async () => {
  // wait async calls and get rendered fragment
  const result = render(<UnavailableErrorPage />, {
    wrapper: TestWrapper,
  });

  expect(result).toMatchSnapshot();
});
