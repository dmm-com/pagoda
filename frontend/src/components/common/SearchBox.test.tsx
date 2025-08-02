/**
 * @jest-environment jsdom
 */

import { fireEvent, render, screen } from "@testing-library/react";

import { SearchBox } from "./SearchBox";

import { TestWrapperWithoutRoutes } from "TestWrapper";

describe("SearchBox", () => {
  // Basic rendering test
  test("renders SearchBox with placeholder", () => {
    render(<SearchBox placeholder="Search here..." />, {
      wrapper: TestWrapperWithoutRoutes,
    });

    const searchInput = screen.getByPlaceholderText("Search here...");
    expect(searchInput).toBeInTheDocument();
  });

  // Test search icon rendering
  test("renders search icon", () => {
    render(<SearchBox placeholder="Search..." />, {
      wrapper: TestWrapperWithoutRoutes,
    });

    // Check if search icon is present - MUI SearchIcon renders as svg
    const searchIcon = document.querySelector("svg");
    expect(searchIcon).toBeInTheDocument();

    // Verify it's in the input adornment
    const inputAdornment = document.querySelector(".MuiInputAdornment-root");
    expect(inputAdornment).toBeInTheDocument();
    expect(inputAdornment).toContainElement(searchIcon);
  });

  // Test controlled value prop
  test("displays controlled value", () => {
    render(<SearchBox placeholder="Search..." value="test value" />, {
      wrapper: TestWrapperWithoutRoutes,
    });

    const searchInput = screen.getByDisplayValue("test value");
    expect(searchInput).toBeInTheDocument();
  });

  // Test defaultValue prop
  test("displays default value", () => {
    render(<SearchBox placeholder="Search..." defaultValue="default value" />, {
      wrapper: TestWrapperWithoutRoutes,
    });

    const searchInput = screen.getByDisplayValue("default value");
    expect(searchInput).toBeInTheDocument();
  });

  // Test onChange handler
  test("calls onChange when input value changes", () => {
    const handleChange = jest.fn();

    render(<SearchBox placeholder="Search..." onChange={handleChange} />, {
      wrapper: TestWrapperWithoutRoutes,
    });

    const searchInput = screen.getByPlaceholderText("Search...");
    fireEvent.change(searchInput, { target: { value: "test" } });

    expect(handleChange).toHaveBeenCalledTimes(1);
    expect(handleChange).toHaveBeenCalledWith(
      expect.objectContaining({
        target: expect.objectContaining({
          value: "test",
        }),
      }),
    );
  });

  // Test onKeyPress handler with Enter key
  test("calls onKeyPress when Enter key is pressed", () => {
    const handleKeyPress = jest.fn();

    render(<SearchBox placeholder="Search..." onKeyPress={handleKeyPress} />, {
      wrapper: TestWrapperWithoutRoutes,
    });

    const searchInput = screen.getByPlaceholderText("Search...");
    // First set the value, then fire the keydown event
    fireEvent.change(searchInput, { target: { value: "search term" } });
    fireEvent.keyDown(searchInput, { key: "Enter" });

    expect(handleKeyPress).toHaveBeenCalledTimes(1);
    expect(handleKeyPress).toHaveBeenCalledWith(
      expect.objectContaining({
        key: "Enter",
      }),
      "search term",
    );
  });

  // Test onKeyPress handler with non-Enter key
  test("does not call onKeyPress when non-Enter key is pressed", () => {
    const handleKeyPress = jest.fn();

    render(<SearchBox placeholder="Search..." onKeyPress={handleKeyPress} />, {
      wrapper: TestWrapperWithoutRoutes,
    });

    const searchInput = screen.getByPlaceholderText("Search...");
    fireEvent.change(searchInput, { target: { value: "test" } });
    fireEvent.keyDown(searchInput, { key: "Escape" });

    expect(handleKeyPress).not.toHaveBeenCalled();
  });

  // Test onKeyPress with empty input
  test("calls onKeyPress with empty string when Enter is pressed on empty input", () => {
    const handleKeyPress = jest.fn();

    render(<SearchBox placeholder="Search..." onKeyPress={handleKeyPress} />, {
      wrapper: TestWrapperWithoutRoutes,
    });

    const searchInput = screen.getByPlaceholderText("Search...");
    fireEvent.focus(searchInput);
    fireEvent.keyDown(searchInput, { key: "Enter" });

    expect(handleKeyPress).toHaveBeenCalledWith(
      expect.objectContaining({
        key: "Enter",
      }),
      "",
    );
  });

  // Test autoFocus prop
  test("focuses input when autoFocus is true", () => {
    render(<SearchBox placeholder="Search..." autoFocus={true} />, {
      wrapper: TestWrapperWithoutRoutes,
    });

    const searchInput = screen.getByPlaceholderText("Search...");
    expect(searchInput).toHaveFocus();
  });

  // Test that input is not focused by default
  test("does not focus input when autoFocus is false", () => {
    render(<SearchBox placeholder="Search..." autoFocus={false} />, {
      wrapper: TestWrapperWithoutRoutes,
    });

    const searchInput = screen.getByPlaceholderText("Search...");
    expect(searchInput).not.toHaveFocus();
  });

  // Test fullWidth prop is applied
  test("renders with fullWidth prop", () => {
    render(<SearchBox placeholder="Search..." />, {
      wrapper: TestWrapperWithoutRoutes,
    });

    const formControl = document.querySelector(".MuiFormControl-root");
    expect(formControl).toHaveClass("MuiFormControl-fullWidth");
  });

  // Test input styling
  test("applies custom styling", () => {
    render(<SearchBox placeholder="Search..." />, {
      wrapper: TestWrapperWithoutRoutes,
    });

    const textField = document.querySelector(".MuiTextField-root");
    expect(textField).toHaveStyle({ background: "#F4F4F4" });
  });

  // Test inputSx prop is applied
  test("applies custom inputSx styling", () => {
    const customSx = { fontSize: "16px" };

    render(<SearchBox placeholder="Search..." inputSx={customSx} />, {
      wrapper: TestWrapperWithoutRoutes,
    });

    const inputProps = document.querySelector(".MuiInputBase-root");
    expect(inputProps).toBeInTheDocument();
  });

  // Test accessibility attributes
  test("has proper accessibility attributes", () => {
    render(<SearchBox placeholder="Search entries..." />, {
      wrapper: TestWrapperWithoutRoutes,
    });

    const searchInput = screen.getByPlaceholderText("Search entries...");
    expect(searchInput).toHaveAttribute("type", "text");
    expect(searchInput).toHaveAttribute("placeholder", "Search entries...");
  });

  // Test that input ref is properly set
  test("input ref is accessible for keyboard events", () => {
    const handleKeyPress = jest.fn();

    render(<SearchBox placeholder="Search..." onKeyPress={handleKeyPress} />, {
      wrapper: TestWrapperWithoutRoutes,
    });

    const searchInput = screen.getByPlaceholderText("Search...");
    fireEvent.change(searchInput, { target: { value: "test input" } });
    fireEvent.keyDown(searchInput, { key: "Enter" });

    expect(handleKeyPress).toHaveBeenCalledWith(
      expect.objectContaining({
        key: "Enter",
      }),
      "test input",
    );
  });

  // Test component re-renders with new defaultValue
  test("re-renders when defaultValue changes", () => {
    const { rerender } = render(
      <SearchBox placeholder="Search..." defaultValue="initial" />,
      { wrapper: TestWrapperWithoutRoutes },
    );

    expect(screen.getByDisplayValue("initial")).toBeInTheDocument();

    rerender(
      <TestWrapperWithoutRoutes>
        <SearchBox placeholder="Search..." defaultValue="updated" />
      </TestWrapperWithoutRoutes>,
    );

    expect(screen.getByDisplayValue("updated")).toBeInTheDocument();
  });

  // Test that both onChange and onKeyPress can work together
  test("handles both onChange and onKeyPress events", () => {
    const handleChange = jest.fn();
    const handleKeyPress = jest.fn();

    render(
      <SearchBox
        placeholder="Search..."
        onChange={handleChange}
        onKeyPress={handleKeyPress}
      />,
      { wrapper: TestWrapperWithoutRoutes },
    );

    const searchInput = screen.getByPlaceholderText("Search...");
    fireEvent.change(searchInput, { target: { value: "test" } });
    fireEvent.keyDown(searchInput, { key: "Enter" });

    expect(handleChange).toHaveBeenCalledTimes(1);
    expect(handleKeyPress).toHaveBeenCalledTimes(1);
  });

  // Test that component works without optional props
  test("works with only required placeholder prop", () => {
    render(<SearchBox placeholder="Minimal search" />, {
      wrapper: TestWrapperWithoutRoutes,
    });

    const searchInput = screen.getByPlaceholderText("Minimal search");
    expect(searchInput).toBeInTheDocument();
  });

  // Test keyboard navigation doesn't trigger onKeyPress for non-Enter keys
  test("ignores non-Enter keyboard events", () => {
    const handleKeyPress = jest.fn();

    render(<SearchBox placeholder="Search..." onKeyPress={handleKeyPress} />, {
      wrapper: TestWrapperWithoutRoutes,
    });

    const searchInput = screen.getByPlaceholderText("Search...");
    fireEvent.change(searchInput, { target: { value: "test" } });
    fireEvent.keyDown(searchInput, { key: "ArrowUp" });
    fireEvent.keyDown(searchInput, { key: "ArrowDown" });
    fireEvent.keyDown(searchInput, { key: "Tab" });

    expect(handleKeyPress).not.toHaveBeenCalled();
  });
});
