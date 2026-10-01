/**
 * UI-facing shape of an import preview.
 *
 * The backend reports the same structure for every importable resource, so the
 * preview components stay independent from the generated API client types.
 */

export type ImportPreviewAction =
  | "create"
  | "update"
  | "unchanged"
  | "skip"
  | "error";

export interface ImportPreviewChange {
  field: string;
  before: string | null;
  after: string | null;
}

export interface ImportPreviewRow {
  index: number;
  kind: string;
  name: string;
  action: ImportPreviewAction;
  reason: string | null;
  changes: ImportPreviewChange[];
  /** Importing this row would fire a trigger, changing values the file omits. */
  willInvokeTrigger: boolean;
}

export interface ImportPreviewSummary {
  created: number;
  updated: number;
  unchanged: number;
  skipped: number;
  errored: number;
  total: number;
}

export const ImportPreviewSummaryKey: Record<
  ImportPreviewAction,
  keyof ImportPreviewSummary
> = {
  create: "created",
  update: "updated",
  unchanged: "unchanged",
  skip: "skipped",
  error: "errored",
};

export interface ImportPreview {
  summary: ImportPreviewSummary;
  rows: ImportPreviewRow[];
  /** How many rows the preview can list; the summary may cover more. */
  count: number;
  /** True when the file has more rows than the preview kept in detail. */
  truncated: boolean;
}

export const ImportPreviewActionLabel: Record<ImportPreviewAction, string> = {
  create: "新規作成",
  update: "更新",
  unchanged: "変更なし",
  skip: "スキップ",
  error: "エラー",
};

export const ImportPreviewSkipReasonLabel: Record<string, string> = {
  spoofing: "作成者が自分ではないため作成できません",
  permission_denied: "更新権限がありません",
  disallow_update: "変更できない項目を変更しようとしています",
};

export const isImportPreviewNoop = (preview: ImportPreview): boolean =>
  preview.summary.created === 0 && preview.summary.updated === 0;
