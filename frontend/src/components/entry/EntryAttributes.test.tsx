/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import * as React from "react";

import { EntryAttributes } from "components/entry/EntryAttributes";
import { TestWrapper } from "utils/TestWrapper";

test("should render a component with essential props", function () {
  const attrs = {};
  expect(() =>
    render(<EntryAttributes attributes={attrs} />, { wrapper: TestWrapper })
  ).not.toThrow();
});
