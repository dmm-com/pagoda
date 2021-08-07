/**
 * @jest-environment jsdom
 */

import React from "react";
import { render } from "@testing-library/react";

import EntryForm from "./EntryForm";

test("should render a component with essential props", function () {
  expect(() => render(<EntryForm entityId={1} />)).not.toThrow();
});
