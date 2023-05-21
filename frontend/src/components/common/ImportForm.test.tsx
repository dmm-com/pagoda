/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { TestWrapper } from "TestWrapper";
import { ImportForm } from "components/common/ImportForm";

test("should render a component with essential props", function () {
  expect(() =>
    render(<ImportForm handleImport={() => Promise.resolve()} />, {
      wrapper: TestWrapper,
    })
  ).not.toThrow();
});
