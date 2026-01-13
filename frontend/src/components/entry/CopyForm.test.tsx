/**
 * @jest-environment jsdom
 */

import { EntryRetrieve } from "@dmm-com/airone-apiclient-typescript-fetch";
import { act, fireEvent, render, screen } from "@testing-library/react";

import { TestWrapper } from "TestWrapper";
import { CopyForm } from "components/entry/CopyForm";
import { ACLType } from "services/ACLUtil";

describe("CopyForm", () => {
  const entry: EntryRetrieve = {
    id: 1,
    name: "entry0001",
    schema: {
      id: 2,
      name: "bbb",
      permission: ACLType.Full,
    },
    attrs: [],
    deletedUser: null,
    isActive: true,
    isPublic: true,
    permission: ACLType.Full,
  };

  test("should set copied entries", function () {
    const setEntries = jest.fn();

    render(
      <CopyForm
        entries="entry1"
        setEntries={setEntries}
        templateEntry={entry}
      />,
      { wrapper: TestWrapper },
    );

    act(() => {
      fireEvent.change(screen.getByPlaceholderText("コピーするアイテム名"), {
        target: { value: "entry1\nentry2" },
      });
    });

    expect(setEntries).toHaveBeenCalledWith("entry1\nentry2");
  });
});
