/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { EntityHistoryList } from "./EntityHistoryList";

import { TestWrapper } from "utils/TestWrapper";

test("should render with essential props", () => {
  expect(() =>
    render(
      <EntityHistoryList
        histories={[]}
        page={1}
        maxPage={1}
        handleChangePage={() => {
          /* nothing */
        }}
      />,
      { wrapper: TestWrapper }
    )
  ).not.toThrow();
});
