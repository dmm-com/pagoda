/**
 * @jest-environment jsdom
 */

import { ThemeProvider, createTheme } from "@mui/material/styles";
import { fireEvent, render, screen } from "@testing-library/react";
import { SnackbarProvider } from "notistack";
import React from "react";
import { MemoryRouter } from "react-router";

import { ImportForm } from "./ImportForm";

// Ensure File is available in the global scope before tests run
if (typeof global.File === "undefined") {
  class MockFile implements Partial<File> {
    readonly name: string;
    readonly size: number;
    readonly type: string;

    constructor(
      chunks: BlobPart[],
      filename: string,
      options?: FilePropertyBag,
    ) {
      this.name = filename;
      this.size = chunks.length > 0 ? 100 : 0;
      this.type = options?.type || "";
    }

    arrayBuffer = jest.fn().mockResolvedValue(new ArrayBuffer(8));
  }

  global.File = MockFile as unknown as typeof File;
}

// Mock encoding-japanese
jest.mock("encoding-japanese", () => ({
  detect: jest.fn().mockReturnValue("UTF-8"),
}));

// Mock react-router
const mockNavigate = jest.fn();
jest.mock("react-router", () => ({
  ...jest.requireActual("react-router"),
  useNavigate: () => mockNavigate,
}));

const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const theme = createTheme();
  return (
    <ThemeProvider theme={theme}>
      <SnackbarProvider maxSnack={1}>
        <MemoryRouter>{children}</MemoryRouter>
      </SnackbarProvider>
    </ThemeProvider>
  );
};

describe("ImportForm", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Ensure File.prototype.arrayBuffer is mocked for encoding detection
    if (global.File && global.File.prototype) {
      global.File.prototype.arrayBuffer = jest
        .fn()
        .mockResolvedValue(new ArrayBuffer(8));
    }
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  test("should render all UI elements", () => {
    const handleImport = jest.fn();

    render(<ImportForm handleImport={handleImport} />, {
      wrapper: TestWrapper,
    });

    expect(screen.getByTestId("upload-import-file")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "インポート" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "キャンセル" }),
    ).toBeInTheDocument();
  });

  test("should handle file selection", () => {
    const handleImport = jest.fn();
    const file = new File(["test content"], "test.yaml", {
      type: "application/yaml",
    });

    render(<ImportForm handleImport={handleImport} />, {
      wrapper: TestWrapper,
    });

    const fileInput = screen.getByTestId("upload-import-file");
    fireEvent.change(fileInput, { target: { files: [file] } });

    expect((fileInput as HTMLInputElement).files).toHaveLength(1);
    expect((fileInput as HTMLInputElement).files![0]).toBe(file);
  });

  test("should not attempt import when no file is selected", () => {
    const handleImport = jest.fn();

    render(<ImportForm handleImport={handleImport} />, {
      wrapper: TestWrapper,
    });

    const importButton = screen.getByRole("button", { name: "インポート" });
    fireEvent.click(importButton);

    expect(handleImport).not.toHaveBeenCalled();
  });
});
