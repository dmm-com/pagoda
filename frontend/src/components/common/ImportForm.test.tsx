/**
 * @jest-environment jsdom
 */

import { ThemeProvider, createTheme } from "@mui/material/styles";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
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

    arrayBuffer = jest.fn().mockResolvedValue(new ArrayBuffer(8));
  }

  global.File = MockFile as unknown as typeof File;
}

// Mock encoding-japanese
jest.mock("encoding-japanese", () => ({
  detect: jest.fn().mockReturnValue("UTF-8"),
  convert: jest.fn().mockReturnValue("Entity: []"),
}));

const mockWaitForImportPreviews = jest.fn();
jest.mock("services/ImportPreviewJob", () => ({
  ...jest.requireActual("services/ImportPreviewJob"),
  waitForImportPreviews: (...args: unknown[]) =>
    mockWaitForImportPreviews(...args),
}));

// Mock react-router
const mockNavigate = jest.fn();
jest.mock("react-router", () => ({
  ...jest.requireActual("react-router"),
  useNavigate: () => mockNavigate,
}));

// MUI's Input puts data-testid on its wrapper, so the actual <input> has to be
// looked up to make React see the change event.
const selectFile = (file: File) => {
  const input = document.querySelector('input[type="file"]');
  if (input == null) {
    throw new Error("file input is not rendered");
  }
  fireEvent.change(input, { target: { files: [file] } });
};

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

  test("should not offer a preview when the caller does not support it", () => {
    render(<ImportForm handleImport={jest.fn()} />, { wrapper: TestWrapper });

    expect(screen.queryByTestId("preview-import-file")).not.toBeInTheDocument();
  });

  test("should show what the file would change before importing it", async () => {
    mockWaitForImportPreviews.mockResolvedValue({
      summary: {
        created: 1,
        updated: 0,
        unchanged: 0,
        skipped: 0,
        errored: 0,
        total: 1,
      },
      count: 1,
      truncated: false,
      rows: [
        {
          index: 0,
          kind: "Entity",
          name: "entity1",
          action: "create",
          reason: null,
          changes: [{ field: "note", before: null, after: "a note" }],
        },
      ],
    });
    const handlePreview = jest.fn().mockResolvedValue([42]);

    render(
      <ImportForm handleImport={jest.fn()} handlePreview={handlePreview} />,
      { wrapper: TestWrapper },
    );

    selectFile(
      new File(["Entity: []"], "entity.yaml", { type: "application/yaml" }),
    );
    fireEvent.click(screen.getByTestId("preview-import-file"));

    await waitFor(() =>
      expect(screen.getByTestId("import-preview")).toBeInTheDocument(),
    );
    expect(handlePreview).toHaveBeenCalledTimes(1);
    // The form starts the jobs and then waits for them; it never previews inline.
    expect(mockWaitForImportPreviews).toHaveBeenCalledWith(
      [42],
      expect.anything(),
    );
    expect(screen.getByText("新規作成 1")).toBeInTheDocument();
    expect(screen.getByText("entity1")).toBeInTheDocument();
    expect(screen.getByText("note: a note")).toBeInTheDocument();
  });

  test("should let the user import without previewing", async () => {
    const handleImport = jest.fn().mockResolvedValue(undefined);
    const handlePreview = jest.fn();

    render(
      <ImportForm handleImport={handleImport} handlePreview={handlePreview} />,
      { wrapper: TestWrapper },
    );

    selectFile(
      new File(["Entity: []"], "entity.yaml", { type: "application/yaml" }),
    );
    fireEvent.click(screen.getByRole("button", { name: "インポート" }));

    await waitFor(() => expect(handleImport).toHaveBeenCalledTimes(1));
    expect(handlePreview).not.toHaveBeenCalled();
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
