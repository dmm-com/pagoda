/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import * as React from "react";

import { CopyForm } from "components/entry/CopyForm";
import { TestWrapper } from "services/TestWrapper";

test("should render a component with essential props", function () {
  const entry = {
    id: 1,
    name: "aaa",
    schema: {
      id: 2,
      name: "bbb",
    },
    attrs: [],
    deletedUser: null,
    isActive: true,
    isPublic: true,
  };

  expect(() =>
    render(
      <CopyForm
        template_entry={entry}
        entries=""
        setEntries={() => {
          /* nothing */
        }}
      />,
      { wrapper: TestWrapper }
    )
  ).not.toThrow();
});
