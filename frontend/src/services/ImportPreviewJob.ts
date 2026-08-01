import { ImportPreview } from "components/common/ImportPreview";
import { aironeApiClient } from "repository/AironeApiClient";
import { ImportPreviewParam, JobStatuses } from "services/Constants";

export class ImportPreviewFailure extends Error {}

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

const statusMessage: Record<number, string> = {
  [JobStatuses.ERROR]: "変更内容の確認に失敗しました",
  [JobStatuses.TIMEOUT]: "変更内容の確認がタイムアウトしました",
  [JobStatuses.CANCELED]: "変更内容の確認を中止しました",
};

/**
 * Wait for a preview job to finish, then read its result.
 *
 * Building a preview costs as much as the import it previews, so the backend
 * runs it on a worker. `onProgress` receives the job's own progress text, which
 * is the only thing that tells the user a large file is still being read.
 */
const mergePreviews = (previews: ImportPreview[]): ImportPreview => ({
  summary: previews.reduce(
    (merged, preview) => ({
      created: merged.created + preview.summary.created,
      updated: merged.updated + preview.summary.updated,
      unchanged: merged.unchanged + preview.summary.unchanged,
      skipped: merged.skipped + preview.summary.skipped,
      errored: merged.errored + preview.summary.errored,
      total: merged.total + preview.summary.total,
    }),
    {
      created: 0,
      updated: 0,
      unchanged: 0,
      skipped: 0,
      errored: 0,
      total: 0,
    },
  ),
  rows: previews.flatMap((preview) => preview.rows),
  count: previews.reduce((total, preview) => total + preview.count, 0),
  truncated: previews.some((preview) => preview.truncated),
});

/**
 * Wait for every preview job of one file, then report them as one preview.
 *
 * An item import file may cover several models, and the backend previews each
 * of them on its own job -- but the user chose one file and expects one answer.
 */
export const waitForImportPreviews = async (
  jobIds: number[],
  options: {
    onProgress?: (text: string) => void;
    isAbandoned?: () => boolean;
  } = {},
): Promise<ImportPreview> =>
  mergePreviews(
    await Promise.all(
      jobIds.map((jobId) => waitForImportPreview(jobId, options)),
    ),
  );

export const waitForImportPreview = async (
  jobId: number,
  {
    onProgress,
    isAbandoned,
  }: {
    onProgress?: (text: string) => void;
    isAbandoned?: () => boolean;
  } = {},
): Promise<ImportPreview> => {
  for (;;) {
    if (isAbandoned?.()) {
      throw new ImportPreviewFailure("変更内容の確認を中止しました");
    }

    const job = await aironeApiClient.getJob(jobId);
    if (job.status === JobStatuses.DONE) {
      return aironeApiClient.getImportPreview(jobId);
    }
    if (job.status != null && job.status in statusMessage) {
      throw new ImportPreviewFailure(statusMessage[job.status]);
    }

    onProgress?.(job.text ?? "");
    await sleep(ImportPreviewParam.POLL_INTERVAL_MS);
  }
};
