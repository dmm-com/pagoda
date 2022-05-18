/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { GroupList } from "components/group/GroupList";
import { TestWrapper } from "utils/TestWrapper";

test("should render a component with essential props", function () {
  expect(() =>
    render(<GroupList groups={[]} />, { wrapper: TestWrapper })
  ).not.toThrow();
});
