/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { TestWrapper } from "../../utils/TestWrapper";

import { EntityList } from "./EntityList";

test("should render with essential props", () => {
  expect(() =>
    render(<EntityList entities={[]} />, { wrapper: TestWrapper })
  ).not.toThrow();
});
