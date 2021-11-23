/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { EntryList } from "./EntryList";

test("should render a component with essential props", function () {
  expect(() =>
    render(<EntryList entityId={"0"} entries={[]} restoreMode={false} />)
  ).not.toThrow();
});
