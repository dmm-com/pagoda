/**
 */

import { EntryRetrieve } from "@dmm-com/airone-apiclient-typescript-fetch";
import { act, render, screen } from "@testing-library/react";

import { EntryBreadcrumbs } from "./EntryBreadcrumbs";

import { TestWrapper } from "TestWrapper";
import i18n from "i18n/config";
import { ACLType } from "services/ACLUtil";

const mockEntry: EntryRetrieve = {
  id: 1,
  name: "TestEntry",
  schema: {
    id: 2,
    name: "TestEntity",
    isPublic: true,
    permission: ACLType.Full,
  },
  isActive: true,
  isPublic: true,
  attrs: [],
  deletedUser: null,
  permission: ACLType.Full,
};

test("should render breadcrumbs with entry", () => {
  render(<EntryBreadcrumbs entry={mockEntry} title="タイトル" />, {
    wrapper: TestWrapper,
  });

  expect(screen.getByText("モデル一覧")).toBeInTheDocument();
  expect(screen.getByText("TestEntity")).toBeInTheDocument();
  expect(screen.getByText("TestEntry")).toBeInTheDocument();
  expect(screen.getByText("タイトル")).toBeInTheDocument();
});

test("renders in English", async () => {
  await act(async () => {
    await i18n.changeLanguage("en");
  });

  render(<EntryBreadcrumbs entry={mockEntry} />, {
    wrapper: TestWrapper,
  });

  expect(screen.getByText("Entity list")).toBeInTheDocument();
});
