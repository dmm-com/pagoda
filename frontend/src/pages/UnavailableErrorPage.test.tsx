/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { UnavailableErrorPage } from "./UnavailableErrorPage";

import { TestWrapper } from "TestWrapper";

afterEach(() => {
  jest.clearAllMocks();
});

test("should match snapshot", async () => {
  // wait async calls and get rendered fragment
  const result = render(<UnavailableErrorPage />, {
    wrapper: TestWrapper,
  });

  expect(result).toMatchSnapshot();
});
