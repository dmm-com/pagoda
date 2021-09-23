/**
 * @jest-environment jsdom
 */

import React from "react";
import { render } from "@testing-library/react";

import CopyForm from "./CopyForm";

test("should render a component with essential props", function () {
  expect(() => render(<CopyForm entityId={"1"} entryId={"1"} />)).not.toThrow();
});
