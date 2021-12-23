/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { TestWrapper } from "../../utils/TestWrapper";

import { UserList } from "./UserList";

test("should render a component with essential props", function () {
  expect(() =>
    render(<UserList users={[]} />, { wrapper: TestWrapper })
  ).not.toThrow();
});
