/**
 */

import { act, render, screen } from "@testing-library/react";

import { UserPasswordFormModal } from "./UserPasswordFormModal";

import { TestWrapper } from "TestWrapper";
import i18n from "i18n/config";

test("should render a component with essential props", function () {
  Object.defineProperty(window, "django_context", {
    value: {
      user: {
        id: 1,
        username: "user1",
        isSuperuser: false,
        isReadonly: false,
        parentUser: null,
        email: "user1@example.com",
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

test("renders in English", async () => {
  await act(async () => {
    await i18n.changeLanguage("en");
  });

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
  );

  expect(screen.getByText("Edit password")).toBeInTheDocument();
});
