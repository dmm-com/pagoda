/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { TestWrapper } from "../utils/TestWrapper";

import { ImportUser } from "./ImportUser";

afterEach(() => {
  jest.clearAllMocks();
});

test("should match snapshot", async () => {
  const result = render(<ImportUser />, {
    wrapper: TestWrapper,
  });

  expect(result).toMatchSnapshot();
});
