/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import EntityList from "./EntityList";

test("should render a component with essential props", function () {
  expect(() => render(<EntityList entities={[]} />)).not.toThrow();
});
