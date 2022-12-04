/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { EntryHistoryList } from "components/entry/EntryHistoryList";
import { TestWrapper } from "utils/TestWrapper";

test("should render a component with essential props", function () {
  expect(() =>
    render(
      <EntryHistoryList
        histories={[]}
        entryId={1}
        page={1}
        maxPage={1}
        handleChangePage={() => {
          /* do nothing */
        }}
      />,
      { wrapper: TestWrapper }
    )
  ).not.toThrow();
});
