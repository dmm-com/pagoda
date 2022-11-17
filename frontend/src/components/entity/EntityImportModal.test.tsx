/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { EntityImportModal } from "./EntityImportModal";

import { TestWrapper } from "utils/TestWrapper";

test("should render a component with essential props", function () {
  expect(() =>
    render(
      <EntityImportModal
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
