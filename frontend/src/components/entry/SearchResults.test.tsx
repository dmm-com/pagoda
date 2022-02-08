/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { SearchResults } from "components/entry/SearchResults";
import { TestWrapper } from "utils/TestWrapper";

test("should render a component with essential props", function () {
  expect(() =>
    render(<SearchResults results={[]} />, { wrapper: TestWrapper })
  ).not.toThrow();
});
