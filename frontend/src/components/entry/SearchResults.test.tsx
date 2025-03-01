/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { TestWrapper } from "TestWrapper";
import { SearchResults } from "components/entry/SearchResults";

test("should render a component with essential props", function () {
  expect(() =>
    render(
      <SearchResults
        results={{
          count: 0,
          values: [],
          totalCount: 0,
        }}
        page={1}
        changePage={() => {
          /* do nothing */
        }}
        bulkOperationEntryIds={[]}
        handleChangeBulkOperationEntryId={() => {
          /* do nothing */
        }}
        hasReferral={false}
        entityIds={[]}
        joinAttrs={[]}
        disablePaginationFooter={false}
        searchAllEntities={false}
        setSearchResults={() => {}}
      />,
      { wrapper: TestWrapper },
    ),
  ).not.toThrow();
});
