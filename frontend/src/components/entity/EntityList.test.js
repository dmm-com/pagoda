/**
 * @jest-environment jsdom
 */

import React from "react";
import { render } from "@testing-library/react";

import EntityList from "./EntityList";

test("should render a component with essential props", function () {
  expect(() => render(<EntityList entities={[]} />)).not.toThrow();
});
