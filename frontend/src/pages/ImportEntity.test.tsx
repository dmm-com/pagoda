/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { TestWrapper } from "../utils/TestWrapper";

import { ImportEntity } from "./ImportEntity";

afterEach(() => {
  jest.clearAllMocks();
});

test("should match snapshot", async () => {
  const result = render(<ImportEntity />, {
    wrapper: TestWrapper,
  });

  expect(result).toMatchSnapshot();
});
