/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { EntryForm } from "components/entry/EntryForm";
import { TestWrapper } from "services/TestWrapper";

test("should render a component with essential props", function () {
  const entryInfo = {
    name: "test entry",
    schema: { id: 0, name: "testEntity" },
    attrs: {},
  };
  const setEntryInfo = () => {
    /* do nothing */
  };
  const setIsAnchorLink = () => {
    /* do nothing */
  };

  expect(() =>
    render(
      <EntryForm
        entryInfo={entryInfo}
        setEntryInfo={setEntryInfo}
        setIsAnchorLink={setIsAnchorLink}
      />,
      {
        wrapper: TestWrapper,
      }
    )
  ).not.toThrow();
});
