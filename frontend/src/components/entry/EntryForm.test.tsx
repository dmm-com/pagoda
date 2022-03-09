/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { EntryForm } from "components/entry/EntryForm";
import { TestWrapper } from "utils/TestWrapper";

test("should render a component with essential props", function () {
  expect(() =>
    render(<EntryForm entityId={1} />, { wrapper: TestWrapper })
  ).not.toThrow();
});
