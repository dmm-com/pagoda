/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { UserImportModal } from "./UserImportModal";

import { TestWrapper } from "services/TestWrapper";

test("should render a component with essential props", function () {
  expect(() =>
    render(
      <UserImportModal
        openImportModal={true}
        closeImportModal={() => {
          /* do nothing */
        }}
      />,
      {
        wrapper: TestWrapper,
      }
    )
  ).not.toThrow();
});
