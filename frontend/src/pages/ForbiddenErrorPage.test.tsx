/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { ForbiddenErrorPage } from "./ForbiddenErrorPage";

import { TestWrapper } from "TestWrapper";

afterEach(() => {
  jest.clearAllMocks();
});

test("should match snapshot", async () => {
  // wait async calls and get rendered fragment
  const result = render(<ForbiddenErrorPage />, {
    wrapper: TestWrapper,
  });

  expect(result).toMatchSnapshot();
});
