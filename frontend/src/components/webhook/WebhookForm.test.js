/**
 * @jest-environment jsdom
 */

import React from "react";
import ReactDOM from "react-dom";
import { act } from "react-dom/test-utils";

import WebhookForm from "./WebhookForm.js";

let container;

beforeEach(() => {
  container = document.createElement("div");
  document.body.appendChild(container);
});

afterEach(() => {
  document.body.removeChild(container);
  container = null;
});

test("should render a component with essential props", function () {
  expect(() => {
    ReactDOM.render(<WebhookForm entityId={0} />, container);
  }).not.toThrow();
});
