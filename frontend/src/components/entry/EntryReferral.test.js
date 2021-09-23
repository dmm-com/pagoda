/**
 * @jest-environment jsdom
 */

import React from "react";
import { render } from "@testing-library/react";

import EntryReferral from "./EntryReferral";
import { BrowserRouter } from "react-router-dom";

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
        <EntryReferral entityId={"1"} referredEntries={referredEntries} />
      </BrowserRouter>
    )
  ).not.toThrow();
});
