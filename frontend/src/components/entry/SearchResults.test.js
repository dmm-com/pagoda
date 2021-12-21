/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { TestWrapper } from "../../utils/TestWrapper";

import { SearchResults } from "./SearchResults";

test("should render a component with essential props", function () {
  expect(() =>
    render(<SearchResults results={[]} />, { wrapper: TestWrapper })
  ).not.toThrow();
});
