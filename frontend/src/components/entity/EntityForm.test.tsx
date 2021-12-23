/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { TestWrapper } from "../../utils/TestWrapper";

import { EntityForm } from "./EntityForm";

test("should render a component with essential props", function () {
  expect(() => render(<EntityForm />, { wrapper: TestWrapper })).not.toThrow();
});
