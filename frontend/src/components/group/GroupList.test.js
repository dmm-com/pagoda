/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { GroupList } from "./GroupList";

test("should render a component with essential props", function () {
  expect(() => render(<GroupList groups={[]} />)).not.toThrow();
});
