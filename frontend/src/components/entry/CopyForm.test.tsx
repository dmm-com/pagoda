/**
 * @jest-environment jsdom
 */

import { EntryRetrieve } from "@dmm-com/airone-apiclient-typescript-fetch";
import { act, fireEvent, render, screen } from "@testing-library/react";
import * as React from "react";

import { TestWrapper } from "TestWrapper";
import { CopyForm } from "components/entry/CopyForm";

describe("CopyForm", () => {
  const entry: EntryRetrieve = {
    id: 1,
    name: "entry0001",
    schema: {
      id: 2,
      name: "bbb",
    },
    attrs: [],
    deletedUser: null,
    isActive: true,
    isPublic: true,
  };

  test("should set copied entries", function () {
    const setEntries = jest.fn();

    render(
      <CopyForm
        entries="entry1"
        setEntries={setEntries}
        templateEntry={entry}
      />,
      { wrapper: TestWrapper }
    );

    act(() => {
      fireEvent.change(screen.getByPlaceholderText("コピーするエントリ名"), {
        target: { value: "entry1\nentry2" },
      });
    });

    expect(setEntries).toHaveBeenCalledWith("entry1\nentry2");
  });
});
