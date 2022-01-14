/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { TestWrapper } from "../utils/TestWrapper";

import { ImportGroup } from "./ImportGroup";

afterEach(() => {
  jest.clearAllMocks();
});

test("should match snapshot", async () => {
  const result = render(<ImportGroup />, {
    wrapper: TestWrapper,
  });

  expect(result).toMatchSnapshot();
});
