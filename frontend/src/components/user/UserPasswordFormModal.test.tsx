/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { UserPasswordFormModal } from "./UserPasswordFormModal";

import { TestWrapper } from "TestWrapper";

test("should render a component with essential props", function () {
  Object.defineProperty(window, "django_context", {
    value: {
      user: {
        is_superuser: false,
      },
    },
    writable: false,
  });

  expect(() =>
    render(
      <UserPasswordFormModal
        userId={1}
        openModal={true}
        onClose={() => {
          /* dummy */
        }}
      />,
      {
        wrapper: TestWrapper,
      },
    ),
  ).not.toThrow();
});
