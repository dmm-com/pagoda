/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { ImportUser } from "pages/ImportUser";
import { TestWrapper } from "utils/TestWrapper";

afterEach(() => {
  jest.clearAllMocks();
});

test("should match snapshot", async () => {
  const result = render(<ImportUser />, {
    wrapper: TestWrapper,
  });

  expect(result).toMatchSnapshot();
});
