/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { PasswordResetModal } from "./PasswordResetModal";

import { TestWrapper } from "utils/TestWrapper";

afterEach(() => {
  jest.clearAllMocks();
});

test("should render a component with essential props", function () {
  expect(() =>
    render(
      <PasswordResetModal
        openModal={true}
        closeModal={() => {
          /* do nothing */
        }}
      />,
      {
        wrapper: TestWrapper,
      }
    )
  ).not.toThrow();
});
