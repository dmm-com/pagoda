/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { ACLHistoryList } from "./ACLHistoryList";

import { TestWrapper } from "TestWrapper";

test("should render with essential props", () => {
  expect(() =>
    render(<ACLHistoryList histories={[]} />, { wrapper: TestWrapper })
  ).not.toThrow();
});
