/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import * as React from "react";

import { EntryAttributes } from "components/entry/EntryAttributes";
import { TestWrapper } from "TestWrapper";

test("should render a component with essential props", function () {
  expect(() =>
    render(<EntryAttributes attributes={[]} />, { wrapper: TestWrapper })
  ).not.toThrow();
});
