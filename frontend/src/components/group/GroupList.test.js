/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { TestWrapper } from "../../utils/TestWrapper";

import { GroupList } from "./GroupList";

test("should render a component with essential props", function () {
  expect(() =>
    render(<GroupList groups={[]} />, { wrapper: TestWrapper })
  ).not.toThrow();
});
