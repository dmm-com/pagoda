/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { EntityList } from "components/entity/EntityList";
import { TestWrapper } from "utils/TestWrapper";

test("should render with essential props", () => {
  expect(() =>
    render(<EntityList entities={[]} />, { wrapper: TestWrapper })
  ).not.toThrow();
});
