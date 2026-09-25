/**
 */

import { act, render, screen } from "@testing-library/react";

import { PasswordResetModal } from "./PasswordResetModal";

import { TestWrapper } from "TestWrapper";
import i18n from "i18n/config";

afterEach(() => {
  vi.clearAllMocks();
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
      },
    ),
  ).not.toThrow();
});

test("renders in English", async () => {
  await act(async () => {
    await i18n.changeLanguage("en");
  });

  render(
    <PasswordResetModal
      openModal={true}
      closeModal={() => {
        /* do nothing */
      }}
    />,
    {
      wrapper: TestWrapper,
    },
  );

  expect(screen.getByText("Password reset")).toBeInTheDocument();
});
