/**
 */

import { act, render, screen } from "@testing-library/react";

import { UserImportModal } from "./UserImportModal";

import { TestWrapper } from "TestWrapper";
import i18n from "i18n/config";

test("should render a component with essential props", function () {
  expect(() =>
    render(
      <UserImportModal
        openImportModal={true}
        closeImportModal={() => {
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
    <UserImportModal
      openImportModal={true}
      closeImportModal={() => {
        /* do nothing */
      }}
    />,
    {
      wrapper: TestWrapper,
    },
  );

  expect(screen.getByText("Import users")).toBeInTheDocument();
});
