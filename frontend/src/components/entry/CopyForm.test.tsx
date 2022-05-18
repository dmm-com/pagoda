/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import * as React from "react";

import { CopyForm } from "components/entry/CopyForm";
import { TestWrapper } from "utils/TestWrapper";

test("should render a component with essential props", function () {
  expect(() =>
    render(<CopyForm entityId={1} entryId={1} />, { wrapper: TestWrapper })
  ).not.toThrow();
});
