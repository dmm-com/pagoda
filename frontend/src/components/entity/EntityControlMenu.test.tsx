/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { EntityControlMenu } from "./EntityControlMenu";

import { TestWrapper } from "TestWrapper";

test("should render with essential props", () => {
  expect(() =>
    render(
      <EntityControlMenu
        entityId={1}
        anchorElem={null}
        handleClose={() => {
          /* any closing process */
        }}
        setOpenImportModal={() => false}
      />,
      { wrapper: TestWrapper },
    ),
  ).not.toThrow();
});
