/**
 * @jest-environment jsdom
 */

import { EntryBase } from "@dmm-com/airone-apiclient-typescript-fetch";
import { render } from "@testing-library/react";

import { TestWrapper } from "TestWrapper";
import { EntryListCard } from "components/entry/EntryListCard";
import { ACLType } from "services/ACLUtil";

afterEach(() => {
  jest.clearAllMocks();
});

test("should render a component with essential props", function () {
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

  expect(() =>
    render(<EntryListCard entityId={1} entry={entry} />, {
      wrapper: TestWrapper,
    }),
  ).not.toThrow();
});
