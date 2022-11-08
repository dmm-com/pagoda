/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { PasswordResetConfirmModal } from "./PasswordResetConfirmModal";

import { TestWrapper } from "utils/TestWrapper";

afterEach(() => {
  jest.clearAllMocks();
});

test("should render a component with essential props", function () {
  expect(() =>
    render(
      <PasswordResetConfirmModal
        openModal={true}
        closeModal={() => {
          /* do nothing */
        }}
        token={"token"}
        uidb64={"uid"}
      />,
      {
        wrapper: TestWrapper,
      }
    )
  ).not.toThrow();
});
