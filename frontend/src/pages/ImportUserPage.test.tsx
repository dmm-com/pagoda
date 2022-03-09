/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { ImportUserPage } from "pages/ImportUserPage";
import { TestWrapper } from "utils/TestWrapper";

afterEach(() => {
  jest.clearAllMocks();
});

test("should match snapshot", async () => {
  const result = render(<ImportUserPage />, {
    wrapper: TestWrapper,
  });

  expect(result).toMatchSnapshot();
});
