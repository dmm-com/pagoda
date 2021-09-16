/**
 * @jest-environment jsdom
 */

import React from "react";
import { render } from "@testing-library/react";

import WebhookForm from "./WebhookForm.js";

test("should render a component with essential props", function () {
  expect(() => render(<WebhookForm entityId={0} />)).not.toThrow();
});
