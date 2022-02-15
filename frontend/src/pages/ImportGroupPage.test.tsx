/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { ImportGroupPage } from "pages/ImportGroupPage";
import { TestWrapper } from "utils/TestWrapper";

afterEach(() => {
  jest.clearAllMocks();
});

test("should match snapshot", async () => {
  const result = render(<ImportGroupPage />, {
    wrapper: TestWrapper,
  });

  expect(result).toMatchSnapshot();
});
