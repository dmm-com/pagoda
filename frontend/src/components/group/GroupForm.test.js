/**
 * @jest-environment jsdom
 */

import React from "react";
import { render } from "@testing-library/react";

import GroupForm from "./GroupForm";

test("should render a component with essential props", function () {
  expect(() => render(<GroupForm users={[]} />)).not.toThrow();
});
