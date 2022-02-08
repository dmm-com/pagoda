/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { GroupForm } from "components/group/GroupForm";
import { TestWrapper } from "utils/TestWrapper";

test("should render a component with essential props", function () {
  expect(() =>
    render(<GroupForm users={[]} />, { wrapper: TestWrapper })
  ).not.toThrow();
});
