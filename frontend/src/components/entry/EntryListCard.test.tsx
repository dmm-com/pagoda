/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";

import { EntryBase } from "@dmm-com/airone-apiclient-typescript-fetch";
import { TestWrapper } from "TestWrapper";
import { EntryListCard } from "components/entry/EntryListCard";

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
    },
    deletedUser: null,
    isActive: true,
    updatedTime: new Date(),
    aliases: [],
  };

  expect(() =>
    render(<EntryListCard entityId={1} entry={entry} />, {
      wrapper: TestWrapper,
    }),
  ).not.toThrow();
});
