/**
 * UI-facing shape of an import preview.
 *
 * The backend reports the same structure for every importable resource, so the
 * preview components stay independent from the generated API client types.
 */

import { translate } from "../../i18n/config";

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

export const importPreviewActionLabel = (
  action: ImportPreviewAction,
): string => {
  switch (action) {
    case "create":
      return translate("importPreview.action.create");
    case "update":
      return translate("importPreview.action.update");
    case "unchanged":
      return translate("importPreview.action.unchanged");
    case "skip":
      return translate("importPreview.action.skip");
    case "error":
      return translate("importPreview.action.error");
  }
};

export const importPreviewSkipReasonLabel = (reason: string): string => {
  switch (reason) {
    case "spoofing":
      return translate("importPreview.skipReason.spoofing");
    case "permission_denied":
      return translate("importPreview.skipReason.permissionDenied");
    case "disallow_update":
      return translate("importPreview.skipReason.disallowUpdate");
    default:
      return reason;
  }
};

export const isImportPreviewNoop = (preview: ImportPreview): boolean =>
  preview.summary.created === 0 && preview.summary.updated === 0;
