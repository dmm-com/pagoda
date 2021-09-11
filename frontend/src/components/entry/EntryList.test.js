/**
 * @jest-environment jsdom
 */

import React from "react";
import { render } from "@testing-library/react";

import { EntryList } from "./EntryList";

test("should render a component with essential props", function () {
  expect(() => render(<EntryList entityId={0} entries={[]} />)).not.toThrow();
});
