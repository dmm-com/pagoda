/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { GroupControlMenu } from "./GroupControlMenu";

import { TestWrapper } from "TestWrapper";

test("should render a component with essential props", function () {
  expect(() =>
    render(
      <GroupControlMenu
        groupId={1}
        anchorElem={null}
        handleClose={() => {
          /* do nothing */
        }}
      />,
      {
        wrapper: TestWrapper,
      },
    ),
  ).not.toThrow();
});
