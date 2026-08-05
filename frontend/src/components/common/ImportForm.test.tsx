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

const mockCancelJob = jest.fn().mockResolvedValue(undefined);
const mockDownloadImportPreview = jest.fn().mockResolvedValue(undefined);
jest.mock("repository/AironeApiClient", () => ({
  aironeApiClient: {
    cancelJob: (...args: unknown[]) => mockCancelJob(...args),
    downloadImportPreview: (...args: unknown[]) =>
      mockDownloadImportPreview(...args),
  },
}));

const mockWaitForImportPreviews = jest.fn();
const mockFetchImportPreviewPage = jest.fn();
jest.mock("services/ImportPreviewJob", () => ({
  ...jest.requireActual("services/ImportPreviewJob"),
  waitForImportPreviews: (...args: unknown[]) =>
    mockWaitForImportPreviews(...args),
  fetchImportPreviewPage: (...args: unknown[]) =>
    mockFetchImportPreviewPage(...args),
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

const previewWith = (
  rows: { index: number; name: string; action: string }[],
) => ({
  summary: {
    created: rows.filter((x) => x.action === "create").length,
    updated: 0,
    unchanged: 0,
    skipped: 0,
    errored: rows.filter((x) => x.action === "error").length,
    total: rows.length,
  },
  count: rows.length,
  truncated: false,
  rows: rows.map((row) => ({
    ...row,
    kind: "Entity",
    reason: null,
    changes: [],
  })),
});

describe("ImportForm", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // The real client returns promises; a bare jest.fn() would not, and the code
    // chains onto what it gets back.
    mockCancelJob.mockResolvedValue(undefined);
    mockDownloadImportPreview.mockResolvedValue(undefined);
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

  test("should re-read the finished jobs when the user filters by action", async () => {
    mockWaitForImportPreviews.mockResolvedValue(
      previewWith([
        { index: 0, name: "ok", action: "create" },
        { index: 1, name: "broken", action: "error" },
      ]),
    );
    mockFetchImportPreviewPage.mockResolvedValue(
      previewWith([{ index: 1, name: "broken", action: "error" }]),
    );

    render(
      <ImportForm
        handleImport={jest.fn()}
        handlePreview={jest.fn().mockResolvedValue([7])}
      />,
      { wrapper: TestWrapper },
    );
    selectFile(new File(["Entity: []"], "entity.yaml"));
    fireEvent.click(screen.getByTestId("preview-import-file"));
    await waitFor(() =>
      expect(screen.getByTestId("import-preview")).toBeInTheDocument(),
    );

    fireEvent.click(screen.getByTestId("import-preview-filter-error"));

    // The file is never uploaded again: the jobs already hold the whole preview.
    await waitFor(() =>
      expect(mockFetchImportPreviewPage).toHaveBeenCalledWith(
        [7],
        expect.objectContaining({ action: ["error"], offset: 0 }),
      ),
    );
    await waitFor(() =>
      expect(screen.queryByText("ok")).not.toBeInTheDocument(),
    );
  });

  test("should append the next page instead of replacing what is shown", async () => {
    mockWaitForImportPreviews.mockResolvedValue({
      ...previewWith([{ index: 0, name: "first", action: "create" }]),
      count: 2,
    });
    mockFetchImportPreviewPage.mockResolvedValue({
      ...previewWith([{ index: 1, name: "second", action: "create" }]),
      count: 2,
    });

    render(
      <ImportForm
        handleImport={jest.fn()}
        handlePreview={jest.fn().mockResolvedValue([7])}
      />,
      { wrapper: TestWrapper },
    );
    selectFile(new File(["Entity: []"], "entity.yaml"));
    fireEvent.click(screen.getByTestId("preview-import-file"));
    await waitFor(() =>
      expect(screen.getByTestId("import-preview")).toBeInTheDocument(),
    );

    fireEvent.click(screen.getByTestId("import-preview-load-more"));

    await waitFor(() => expect(screen.getByText("second")).toBeInTheDocument());
    expect(screen.getByText("first")).toBeInTheDocument();
    expect(mockFetchImportPreviewPage).toHaveBeenCalledWith(
      [7],
      expect.objectContaining({ offset: 1 }),
    );
  });

  test("should let the user give up on a preview that is still running", async () => {
    // Previewing a large file takes as long as importing it, so the wait has to
    // be escapable -- which is why previews run as cancelable jobs.
    mockWaitForImportPreviews.mockReturnValue(new Promise(() => {}));

    render(
      <ImportForm
        handleImport={jest.fn()}
        handlePreview={jest.fn().mockResolvedValue([7, 8])}
      />,
      { wrapper: TestWrapper },
    );
    selectFile(new File(["Entity: []"], "entity.yaml"));
    fireEvent.click(screen.getByTestId("preview-import-file"));

    await waitFor(() =>
      expect(screen.getByTestId("cancel-import-preview")).toBeInTheDocument(),
    );
    fireEvent.click(screen.getByTestId("cancel-import-preview"));

    await waitFor(() => expect(mockCancelJob).toHaveBeenCalledWith(7));
    expect(mockCancelJob).toHaveBeenCalledWith(8);
  });

  test("should hand the approved preview to the import", async () => {
    const handleImport = jest.fn().mockResolvedValue(undefined);
    mockWaitForImportPreviews.mockResolvedValue(
      previewWith([{ index: 0, name: "ok", action: "create" }]),
    );

    render(
      <ImportForm
        handleImport={handleImport}
        handlePreview={jest.fn().mockResolvedValue([7])}
      />,
      { wrapper: TestWrapper },
    );
    selectFile(new File(["Entity: []"], "entity.yaml"));
    fireEvent.click(screen.getByTestId("preview-import-file"));
    await waitFor(() =>
      expect(screen.getByTestId("import-preview")).toBeInTheDocument(),
    );

    fireEvent.click(screen.getByRole("button", { name: "インポート" }));

    // The import needs to know which preview was approved, so that it can leave
    // alone anything changed since.
    await waitFor(() =>
      expect(handleImport).toHaveBeenCalledWith(expect.anything(), [7]),
    );
  });

  test("should let the user download the whole preview", async () => {
    mockWaitForImportPreviews.mockResolvedValue(
      previewWith([{ index: 0, name: "ok", action: "create" }]),
    );

    render(
      <ImportForm
        handleImport={jest.fn()}
        handlePreview={jest.fn().mockResolvedValue([7])}
      />,
      { wrapper: TestWrapper },
    );
    selectFile(new File(["Entity: []"], "entity.yaml"));
    fireEvent.click(screen.getByTestId("preview-import-file"));
    await waitFor(() =>
      expect(screen.getByTestId("import-preview")).toBeInTheDocument(),
    );

    fireEvent.click(screen.getByTestId("import-preview-download"));

    await waitFor(() =>
      expect(mockDownloadImportPreview).toHaveBeenCalledWith(
        7,
        "import_preview.csv",
      ),
    );
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
