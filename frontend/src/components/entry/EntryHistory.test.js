/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import EntryHistory from "./EntryHistory";

test("should render a component with essential props", function () {
  const histories = [
    {
      attr_name: "test",
      prev: {
        created_user: "admin",
        created_time: new Date().toDateString(),
        value: "before",
      },
      curr: {
        created_user: "admin",
        created_time: new Date().toDateString(),
        value: "after",
      },
    },
  ];
  expect(() => render(<EntryHistory histories={histories} />)).not.toThrow();
});
