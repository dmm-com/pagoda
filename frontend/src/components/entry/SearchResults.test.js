/**
 * @jest-environment jsdom
 */

import { Router } from "@material-ui/icons";
import { render } from "@testing-library/react";
import React from "react";

import { SearchResults } from "./SearchResults";

test("should render a component with essential props", function () {
  expect(() =>
    render(
      <Router>
        <SearchResults results={[]} />
      </Router>
    )
  ).not.toThrow();
});
