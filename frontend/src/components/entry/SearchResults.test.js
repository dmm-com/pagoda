/**
 * @jest-environment jsdom
 */

import React from "react";
import { render } from "@testing-library/react";

import SearchResults from "./SearchResults";
import { Router } from "@material-ui/icons";

test("should render a component with essential props", function () {
  expect(() =>
    render(
      <Router>
        <SearchResults results={[]} />
      </Router>
    )
  ).not.toThrow();
});
