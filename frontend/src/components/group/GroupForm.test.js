/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { TestWrapper } from "../../utils/TestWrapper";

import { GroupForm } from "./GroupForm";

test("should render a component with essential props", function () {
  expect(() =>
    render(<GroupForm users={[]} />, { wrapper: TestWrapper })
  ).not.toThrow();
});
