/**
 */

import { ThemeProvider, createTheme } from "@mui/material/styles";
import { fireEvent, render, screen } from "@testing-library/react";
import { SnackbarProvider } from "notistack";
import { FC, ReactNode } from "react";
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

    arrayBuffer = vi.fn().mockResolvedValue(new ArrayBuffer(8));
  }

  global.File = MockFile as unknown as typeof File;
}

// Mock encoding-japanese
vi.mock("encoding-japanese", () => ({
  detect: vi.fn().mockReturnValue("UTF-8"),
}));

// Mock react-router
const mockNavigate = vi.fn();
vi.mock("react-router", async () => ({
  ...((await vi.importActual("react-router")) as object),
  useNavigate: () => mockNavigate,
}));

const TestWrapper: FC<{ children: ReactNode }> = ({ children }) => {
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
    vi.clearAllMocks();
    // Ensure File.prototype.arrayBuffer is mocked for encoding detection
    if (global.File && global.File.prototype) {
      global.File.prototype.arrayBuffer = vi
        .fn()
        .mockResolvedValue(new ArrayBuffer(8));
    }
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  test("should render all UI elements", () => {
    const handleImport = vi.fn();

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
    const handleImport = vi.fn();
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
    const handleImport = vi.fn();

    render(<ImportForm handleImport={handleImport} />, {
      wrapper: TestWrapper,
    });

    const importButton = screen.getByRole("button", { name: "インポート" });
    fireEvent.click(importButton);

    expect(handleImport).not.toHaveBeenCalled();
  });
});
