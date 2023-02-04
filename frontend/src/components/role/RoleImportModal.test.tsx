/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { RoleImportModal } from "./RoleImportModal";

import { TestWrapper } from "services/TestWrapper";

test("should render a component with essential props", function () {
  expect(() =>
    render(
      <RoleImportModal
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
