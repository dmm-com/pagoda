/**
 * @jest-environment jsdom
 */

import React from "react";
import { render } from "@testing-library/react";

import { UserList } from "./UserList";

test("should render a component with essential props", function () {
  expect(() => render(<UserList users={[]} />)).not.toThrow();
});
