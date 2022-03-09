/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { EntryControlMenu } from "components/entry/EntryControlMenu";
import { TestWrapper } from "utils/TestWrapper";

test("should render a component with essential props", function () {
  const anchorElem = document.createElement("button");
  const handleClose = () => undefined;

  expect(() =>
    render(
      <EntryControlMenu
        entryId={0}
        anchorElem={anchorElem}
        handleClose={handleClose}
      />,
      {
        wrapper: TestWrapper,
      }
    )
  ).not.toThrow();
});
