/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { SearchResultsTableHead } from "./SearchResultsTableHead";

import { TestWrapper } from "TestWrapper";

describe("SearchResultsTableHead", () => {
  const defaultProps = {
    hasReferral: false,
    attrTypes: {},
    entityIds: [1, 2],
    searchAllEntities: false,
    joinAttrs: [],
    handleChangeAllBulkOperationEntryIds: jest.fn(),
  };

  test("should render without crashing", () => {
    expect(() =>
      render(<SearchResultsTableHead {...defaultProps} />, {
        wrapper: TestWrapper,
      }),
    ).not.toThrow();
  });
});
