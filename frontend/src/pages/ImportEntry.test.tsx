/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { TestWrapper } from "../utils/TestWrapper";

import { ImportEntry } from "./ImportEntry";

afterEach(() => {
  jest.clearAllMocks();
});

test("should match snapshot", async () => {
  const result = render(<ImportEntry />, {
    wrapper: TestWrapper,
  });

  expect(result).toMatchSnapshot();
});
