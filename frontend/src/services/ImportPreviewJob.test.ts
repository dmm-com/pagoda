import { vi } from "vitest";

import {
  ImportPreviewFailure,
  waitForImportPreview,
  waitForImportPreviews,
} from "./ImportPreviewJob";

import { JobStatuses } from "services/Constants";

const mockGetJob = vi.fn();
const mockGetImportPreview = vi.fn();

vi.mock("repository/AironeApiClient", () => ({
  aironeApiClient: {
    getJob: (...args: unknown[]) => mockGetJob(...args),
    getImportPreview: (...args: unknown[]) => mockGetImportPreview(...args),
  },
}));

vi.mock("services/Constants", async () => ({
  ...(await vi.importActual<typeof import("services/Constants")>(
    "services/Constants",
  )),
  ImportPreviewParam: { MAX_ROW_COUNT: 200, POLL_INTERVAL_MS: 0 },
}));

describe("waitForImportPreview", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test("should report progress until the job is done, then read the preview", async () => {
    mockGetJob
      .mockResolvedValueOnce({
        status: JobStatuses.PREPARING,
        text: "Preparing",
      })
      .mockResolvedValueOnce({
        status: JobStatuses.PROCESSING,
        text: "Now previewing... (progress: [    2/   10])",
      })
      .mockResolvedValueOnce({ status: JobStatuses.DONE, text: "" });
    mockGetImportPreview.mockResolvedValue({ rows: [] });

    const onProgress = vi.fn();
    await expect(waitForImportPreview(7, { onProgress })).resolves.toEqual({
      rows: [],
    });

    expect(onProgress).toHaveBeenNthCalledWith(1, "Preparing");
    expect(onProgress).toHaveBeenNthCalledWith(
      2,
      "Now previewing... (progress: [    2/   10])",
    );
    expect(mockGetImportPreview).toHaveBeenCalledWith(7, {
      offset: undefined,
      limit: undefined,
      action: undefined,
    });
  });

  test.each([
    [JobStatuses.ERROR, "変更内容の確認に失敗しました"],
    [JobStatuses.TIMEOUT, "変更内容の確認がタイムアウトしました"],
    [JobStatuses.CANCELED, "変更内容の確認を中止しました"],
  ])("should fail on job status %i", async (status, message) => {
    mockGetJob.mockResolvedValue({ status, text: "" });

    await expect(waitForImportPreview(7)).rejects.toThrow(
      new ImportPreviewFailure(message),
    );
    expect(mockGetImportPreview).not.toHaveBeenCalled();
  });

  test("should report the preview jobs of one file as a single preview", async () => {
    mockGetJob.mockResolvedValue({ status: JobStatuses.DONE, text: "" });
    mockGetImportPreview
      .mockResolvedValueOnce({
        summary: {
          created: 2,
          updated: 0,
          unchanged: 1,
          skipped: 0,
          errored: 0,
          total: 3,
        },
        count: 3,
        truncated: false,
        rows: [{ name: "a" }],
      })
      .mockResolvedValueOnce({
        summary: {
          created: 0,
          updated: 1,
          unchanged: 0,
          skipped: 0,
          errored: 1,
          total: 2,
        },
        count: 2,
        truncated: true,
        rows: [{ name: "b" }],
      });

    // An item import file may cover several models; the user still chose one file.
    const merged = await waitForImportPreviews([1, 2]);

    expect(merged.summary).toEqual({
      created: 2,
      updated: 1,
      unchanged: 1,
      skipped: 0,
      errored: 1,
      total: 5,
    });
    expect(merged.count).toBe(5);
    expect(merged.truncated).toBe(true);
    expect(merged.rows).toEqual([{ name: "a" }, { name: "b" }]);
  });

  test("should stop polling once the caller has abandoned the job", async () => {
    mockGetJob.mockResolvedValue({
      status: JobStatuses.PROCESSING,
      text: "",
    });

    await expect(
      waitForImportPreview(7, { isAbandoned: () => true }),
    ).rejects.toThrow(ImportPreviewFailure);
    expect(mockGetJob).not.toHaveBeenCalled();
  });
});
