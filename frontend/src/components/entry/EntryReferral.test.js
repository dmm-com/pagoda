/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";
import { BrowserRouter } from "react-router-dom";

import EntryReferral from "./EntryReferral";

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
