/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { TestWrapper } from "TestWrapper";
import { SearchResults } from "components/entry/SearchResults";

test("should render a component with essential props", function () {
  expect(() =>
    render(
      <SearchResults
        results={[]}
        page={1}
        maxPage={1}
        handleChangePage={() => {
          /* do nothing */
        }}
      />,
      { wrapper: TestWrapper }
    )
  ).not.toThrow();
});
