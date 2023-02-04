/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { EntityList } from "components/entity/EntityList";
import { TestWrapper } from "services/TestWrapper";

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
