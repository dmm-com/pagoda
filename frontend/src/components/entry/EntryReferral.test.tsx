/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";
import { BrowserRouter } from "react-router-dom";

import { EntryReferral } from "components/entry/EntryReferral";
import { TestWrapper } from "utils/TestWrapper";

test("should render a component with essential props", function () {
  const referredEntries = [
    {
      id: 1,
      name: "name",
      entity: "entity",
    },
  ];
  expect(() =>
    render(
      <BrowserRouter>
        <EntryReferral referredEntries={referredEntries} />
      </BrowserRouter>,
      { wrapper: TestWrapper }
    )
  ).not.toThrow();
});
