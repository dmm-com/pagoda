/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { TestWrapper } from "TestWrapper";
import { EntityList } from "components/entity/EntityList";

test("should render with essential props", () => {
  expect(() =>
    render(
      <EntityList
        entities={[]}
        page={1}
        query=""
        maxPage={1}
        handleChangePage={() => {
          /* nothing */
        }}
        handleChangeQuery={() => {
          /* nothing */
        }}
      />,
      { wrapper: TestWrapper }
    )
  ).not.toThrow();
});
