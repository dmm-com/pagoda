/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { TestWrapper } from "../../utils/TestWrapper";

import { EntryForm } from "./EntryForm";

test("should render a component with essential props", function () {
  expect(() =>
    render(<EntryForm entityId={1} />, { wrapper: TestWrapper })
  ).not.toThrow();
});
