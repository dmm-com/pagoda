/**
 * @jest-environment jsdom
 */

import React from "react";
import { render } from "@testing-library/react";

import GroupList from "./GroupList";

test("should render a component with essential props", function () {
  expect(() => render(<GroupList groups={[]} />)).not.toThrow();
});
