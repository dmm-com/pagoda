/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";
import { BrowserRouter } from "react-router-dom";

import { TestWrapper } from "../../utils/TestWrapper";

import { EntryReferral } from "./EntryReferral";

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
