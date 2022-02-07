/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { ImportEntity } from "pages/ImportEntity";
import { TestWrapper } from "utils/TestWrapper";

afterEach(() => {
  jest.clearAllMocks();
});

test("should match snapshot", async () => {
  const result = render(<ImportEntity />, {
    wrapper: TestWrapper,
  });

  expect(result).toMatchSnapshot();
});
