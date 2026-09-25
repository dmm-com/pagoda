/**
 */

import { act, render, screen } from "@testing-library/react";

import { GroupImportModal } from "./GroupImportModal";

import { TestWrapper } from "TestWrapper";
import i18n from "i18n/config";

test("should render a component with essential props", function () {
  expect(() =>
    render(
      <GroupImportModal
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
    <GroupImportModal
      openImportModal={true}
      closeImportModal={() => {
        /* do nothing */
      }}
    />,
    {
      wrapper: TestWrapper,
    },
  );

  expect(screen.getByText("Import groups")).toBeInTheDocument();
});
