/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { EntryForm } from "components/entry/EntryForm";
import { TestWrapper } from "utils/TestWrapper";

test("should render a component with essential props", function () {
  const entryInfo = { name: "test entry", attrs: {} };
  const setEntryInfo = () => {
    /* do nothing */
  };

  expect(() =>
    render(<EntryForm entryInfo={entryInfo} setEntryInfo={setEntryInfo} />, {
      wrapper: TestWrapper,
    })
  ).not.toThrow();
});
