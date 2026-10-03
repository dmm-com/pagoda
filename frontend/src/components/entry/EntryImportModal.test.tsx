/**
 */

import { act, render, screen } from "@testing-library/react";

import { EntryImportModal } from "./EntryImportModal";

import { TestWrapper } from "TestWrapper";
import i18n from "i18n/config";

test("should render import modal", () => {
  render(
    <EntryImportModal openImportModal={true} closeImportModal={vi.fn()} />,
    { wrapper: TestWrapper },
  );

  expect(screen.getByText("アイテムのインポート")).toBeInTheDocument();
  expect(
    screen.getByText("インポートするファイルを選択してください。"),
  ).toBeInTheDocument();
  expect(
    screen.getByText("※CSV形式のファイルは選択できません。"),
  ).toBeInTheDocument();
});

test("renders in English", async () => {
  await act(async () => {
    await i18n.changeLanguage("en");
  });

  render(
    <EntryImportModal openImportModal={true} closeImportModal={vi.fn()} />,
    { wrapper: TestWrapper },
  );

  expect(screen.getByText("Import entries")).toBeInTheDocument();
  expect(
    screen.getByText("Please select a file to import."),
  ).toBeInTheDocument();
  expect(
    screen.getByText("* Files in CSV format cannot be selected."),
  ).toBeInTheDocument();
});
