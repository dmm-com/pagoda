/**
 * @jest-environment jsdom
 */

import { EntryBase } from "@dmm-com/airone-apiclient-typescript-fetch";
import { render } from "@testing-library/react";
import React from "react";

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
  };

  expect(() =>
    render(<EntryListCard entityId={1} entry={entry} />, {
      wrapper: TestWrapper,
    })
  ).not.toThrow();
});
