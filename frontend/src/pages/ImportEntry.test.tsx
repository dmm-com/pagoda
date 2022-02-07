/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { ImportEntry } from "pages/ImportEntry";
import { TestWrapper } from "utils/TestWrapper";

afterEach(() => {
  jest.clearAllMocks();
});

test("should match snapshot", async () => {
  const result = render(<ImportEntry />, {
    wrapper: TestWrapper,
  });

  expect(result).toMatchSnapshot();
});
