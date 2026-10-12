/**
 */

import { EntryBase } from "@dmm-com/airone-apiclient-typescript-fetch";
import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";

import { TestWrapper } from "TestWrapper";
import { EntryListCard } from "components/entry/EntryListCard";
import i18n from "i18n/config";
import { ACLType } from "services/ACLUtil";

afterEach(() => {
  vi.clearAllMocks();
});

const entry: EntryBase = {
  id: 1,
  name: "TestEntry",
  schema: {
    id: 2,
    name: "TestEntity",
    permission: ACLType.Full,
  },
  deletedUser: null,
  isActive: true,
  updatedTime: new Date(),
  aliases: [],
  permission: ACLType.Full,
};

test("should render a component with essential props", function () {
  expect(() =>
    render(<EntryListCard entityId={1} entry={entry} />, {
      wrapper: TestWrapper,
    }),
  ).not.toThrow();
});

test("renders in English", async () => {
  await act(async () => {
    await i18n.changeLanguage("en");
  });

  render(<EntryListCard entityId={1} entry={entry} />, {
    wrapper: TestWrapper,
  });

  fireEvent.mouseOver(screen.getByTestId("MoreVertIcon"));

  await waitFor(() => {
    expect(screen.getByText("Entry operations")).toBeInTheDocument();
  });
});
