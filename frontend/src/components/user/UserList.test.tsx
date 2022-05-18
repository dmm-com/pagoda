/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { UserList } from "components/user/UserList";
import { TestWrapper } from "utils/TestWrapper";

test("should render a component with essential props", function () {
  expect(() =>
    render(<UserList users={[]} />, { wrapper: TestWrapper })
  ).not.toThrow();
});
