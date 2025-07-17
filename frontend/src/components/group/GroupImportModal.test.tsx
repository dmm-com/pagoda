/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { GroupImportModal } from "./GroupImportModal";

import { TestWrapper } from "TestWrapper";

test("should render a component with essential props", function () {
  expect(() =>
    render(
      <GroupImportModal
        openImportModal={true}
        closeImportModal={() => {
          /* do nothing */
        }}
      />,
      {
        wrapper: TestWrapper,
      },
    ),
  ).not.toThrow();
});
