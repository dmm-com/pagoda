/**
 */

import { act, render, screen } from "@testing-library/react";

import { PasswordResetConfirmModal } from "./PasswordResetConfirmModal";

import { TestWrapper } from "TestWrapper";
import i18n from "i18n/config";

afterEach(() => {
  vi.clearAllMocks();
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
      },
    ),
  ).not.toThrow();
});

test("renders in English", async () => {
  await act(async () => {
    await i18n.changeLanguage("en");
  });

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
    },
  );

  expect(screen.getByText("Password reset")).toBeInTheDocument();
});
