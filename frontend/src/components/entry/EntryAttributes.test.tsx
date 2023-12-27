/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import * as React from "react";

import { TestWrapper } from "TestWrapper";
import { EntryAttributes } from "components/entry/EntryAttributes";

test("should render a component with essential props", function () {
  expect(() =>
    render(<EntryAttributes attributes={[]} />, { wrapper: TestWrapper }),
  ).not.toThrow();
});
