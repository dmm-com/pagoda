/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { ImportEntityPage } from "pages/ImportEntityPage";
import { TestWrapper } from "utils/TestWrapper";

afterEach(() => {
  jest.clearAllMocks();
});

test("should match snapshot", async () => {
  const result = render(<ImportEntityPage />, {
    wrapper: TestWrapper,
  });

  expect(result).toMatchSnapshot();
});
