/**
 * @jest-environment jsdom
 */

import { EntryRetrieve } from "@dmm-com/airone-apiclient-typescript-fetch";
import { render } from "@testing-library/react";
import * as React from "react";

import { TestWrapper } from "TestWrapper";
import { CopyForm } from "components/entry/CopyForm";

test("should render a component with essential props", function () {
  const entry: EntryRetrieve = {
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
        entries=""
        setEntries={() => {
          /* nothing */
        }}
        templateEntry={entry}
      />,
      { wrapper: TestWrapper }
    )
  ).not.toThrow();
});
