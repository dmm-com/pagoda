/**
 * @jest-environment jsdom
 */

import { screen } from "@testing-library/dom";
import { fireEvent, render } from "@testing-library/react";
import React from "react";
import { MemoryRouter } from "react-router-dom";

import { EntityList } from "./EntityList";

test("should render with essential props", () => {
  expect(() => render(<EntityList entities={[]} />)).not.toThrow();
});

test("should filter entities with given keyword", () => {
  const entities = [
    {
      id: "1",
      name: "aaa",
      note: "",
    },
    {
      id: "2",
      name: "aaaaa",
      note: "",
    },
    {
      id: "3",
      name: "bbbbb",
      note: "",
    },
  ];

  render(<EntityList entities={entities} />, {
    wrapper: MemoryRouter,
  });

  fireEvent.change(screen.getByTestId("entityName"), {
    target: { value: "aaa" },
  });

  expect(screen.getAllByTestId("entityTableRow").length).toEqual(2);
});
