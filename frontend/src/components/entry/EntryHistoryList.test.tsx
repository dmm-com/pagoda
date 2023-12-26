/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { TestWrapper } from "TestWrapper";
import { EntryHistoryList } from "components/entry/EntryHistoryList";

test("should render a component with essential props", function () {
  expect(() =>
    render(
      <EntryHistoryList
        entityId={2}
        entryId={1}
        histories={[]}
        totalPageCount={1}
        maxRowCount={1}
        page={1}
        changePage={() => {
          /* do nothing */
        }}
      />,
      { wrapper: TestWrapper }
    )
  ).not.toThrow();
});
