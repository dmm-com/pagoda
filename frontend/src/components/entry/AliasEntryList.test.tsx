/**
 * @jest-environment jsdom
 */

import { render, screen, fireEvent } from "@testing-library/react";

import "@testing-library/jest-dom";

import { AliasEntryList } from "./AliasEntryList";

import { EntryBase } from "@dmm-com/airone-apiclient-typescript-fetch";
import { ACLType } from "services/ACLUtil";

const mockHandleCreate = jest.fn();
const mockHandleDelete = jest.fn();

const mockEntryBase: EntryBase = {
  id: 123,
  name: "Test Entry",
  schema: { id: 1, name: "Mock Schema", permission: ACLType.Full },
  isActive: true,
  deletedUser: null,
  updatedTime: new Date(),
  aliases: [
    { id: 1, name: "Alias One", entry: 123 },
    { id: 2, name: "Alias Two", entry: 123 },
  ],
  permission: ACLType.Full,
};

// Helper function to render the component
const renderComponent = (entryProps: EntryBase = mockEntryBase) => {
  return render(
    <AliasEntryList
      entry={entryProps}
      handleCreate={mockHandleCreate}
      handleDelete={mockHandleDelete}
    />,
  );
};

describe("AliasEntryList Component", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("renders existing aliases as chips", () => {
    renderComponent();
    expect(screen.getByText("Alias One")).toBeInTheDocument();
    expect(screen.getByText("Alias Two")).toBeInTheDocument();
    expect(screen.getAllByTestId("CancelIcon")).toHaveLength(2);
  });

  test("calls handleDelete when a chip delete icon is clicked", () => {
    renderComponent();
    const deleteButtonOne = screen.getAllByTestId("CancelIcon")[0];
    fireEvent.click(deleteButtonOne);
    expect(mockHandleDelete).toHaveBeenCalledTimes(1);
    expect(mockHandleDelete).toHaveBeenCalledWith(1);

    const deleteButtonTwo = screen.getAllByTestId("CancelIcon")[1];
    fireEvent.click(deleteButtonTwo);
    expect(mockHandleDelete).toHaveBeenCalledTimes(2);
    expect(mockHandleDelete).toHaveBeenCalledWith(2);
  });

  test("shows add alias input when add icon chip is clicked", () => {
    renderComponent();
    expect(
      screen.queryByPlaceholderText("エイリアスを追加"),
    ).not.toBeInTheDocument();

    const addChipButton = screen.getByTestId("AddIcon");
    fireEvent.click(addChipButton);

    expect(screen.getByPlaceholderText("エイリアスを追加")).toBeInTheDocument();
    expect(screen.queryByTestId("AddIcon")).not.toBeInTheDocument();
  });

  test("calls handleCreate when Enter is pressed in the add alias input", () => {
    renderComponent();
    const addChipButton = screen.getByTestId("AddIcon");
    fireEvent.click(addChipButton);

    const inputField = screen.getByPlaceholderText("エイリアスを追加");
    const newAliasName = "New Alias Three";

    fireEvent.change(inputField, { target: { value: newAliasName } });
    fireEvent.keyDown(inputField, {
      key: "Enter",
      code: "Enter",
      charCode: 13,
    });

    expect(mockHandleCreate).toHaveBeenCalledTimes(1);
    expect(mockHandleCreate).toHaveBeenCalledWith(mockEntryBase.id, inputField);
    expect((inputField as HTMLInputElement).value).toBe(newAliasName);
  });

  test("renders correctly with no aliases", () => {
    const entryWithoutAliases: EntryBase = {
      ...mockEntryBase,
      aliases: [],
    };
    renderComponent(entryWithoutAliases);
    expect(screen.queryByText("Alias One")).not.toBeInTheDocument();
    expect(screen.queryByText("Alias Two")).not.toBeInTheDocument();
    expect(screen.getByTestId("AddIcon")).toBeInTheDocument();
  });
});
