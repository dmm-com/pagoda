/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { LoginPage } from "./LoginPage";

import { TestWrapper } from "TestWrapper";

afterEach(() => {
  jest.clearAllMocks();
});

test("should match snapshot", async () => {
  Object.defineProperty(window, "django_context", {
    value: {
      title: "AirOne",
      password_reset_disabled: "False"
    },
    writable: false,
  });

  const result = render(<LoginPage />, {
    wrapper: TestWrapper,
  });

  expect(result).toMatchSnapshot();
});
