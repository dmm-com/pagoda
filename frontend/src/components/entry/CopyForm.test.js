/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import CopyForm from "./CopyForm";

test("should render a component with essential props", function () {
  expect(() => render(<CopyForm entityId={1} entryId={"1"} />)).not.toThrow();
});
