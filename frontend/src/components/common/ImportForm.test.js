/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { ImportForm } from "./ImportForm";

test("should render a component with essential props", function () {
  expect(() =>
    render(
      <ImportForm importFunc={() => {}} redirectPath={"/path/to/redirect"} />
    )
  ).not.toThrow();
});
