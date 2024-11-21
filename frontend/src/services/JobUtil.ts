import { JobSerializers } from "@dmm-com/airone-apiclient-typescript-fetch";

import {
  LocalStorageKey,
  localStorageUtil,
} from "../repository/LocalStorageUtil";

import { JobOperations, JobStatuses } from "./Constants";

export const jobStatusLabel = (jobStatus: number | undefined): string => {
  switch (jobStatus) {
    case JobStatuses.PREPARING:
      return "処理前";
    case JobStatuses.DONE:
      return "完了";
    case JobStatuses.ERROR:
      return "失敗";
    case JobStatuses.TIMEOUT:
      return "タイムアウト";
    case JobStatuses.PROCESSING:
      return "処理中";
    case JobStatuses.CANCELED:
      return "キャンセル";
    default:
      return "不明";
  }
};

interface CustomJobOperationType {
  operation: number;
  label: string;
}
let customJobOperations: CustomJobOperationType[] = [];

export const setCustomJobOperations = (
  customCondition: CustomJobOperationType[]
) => {
  customJobOperations = customCondition;
};

export const jobOperationLabel = (jobOperation: number | undefined): string => {
  // This shows Job label that is declared by customView
  for (const condition of customJobOperations) {
    if (jobOperation === condition.operation) {
      return condition.label;
    }
  }

  switch (jobOperation) {
    case JobOperations.CREATE_ENTRY:
    case JobOperations.CREATE_ENTITY:
    case JobOperations.CREATE_ENTITY_V2:
    case JobOperations.CREATE_ENTRY_V2:
      return "作成";
    case JobOperations.EDIT_ENTRY:
    case JobOperations.EDIT_ENTITY:
    case JobOperations.EDIT_ENTITY_V2:
    case JobOperations.EDIT_ENTRY_V2:
      return "編集";
    case JobOperations.DELETE_ENTITY:
    case JobOperations.DELETE_ENTRY:
    case JobOperations.DELETE_ENTITY_V2:
    case JobOperations.DELETE_ENTRY_V2:
      return "削除";
    case JobOperations.IMPORT_ENTRY:
    case JobOperations.IMPORT_ENTRY_V2:
      return "インポート";
    case JobOperations.EXPORT_ENTRY:
    case JobOperations.EXPORT_SEARCH_RESULT:
    case JobOperations.EXPORT_ENTRY_V2:
    case JobOperations.EXPORT_SEARCH_RESULT_V2:
      return "エクスポート";
    case JobOperations.COPY_ENTRY:
    case JobOperations.DO_COPY_ENTRY:
      return "コピー";
    case JobOperations.RESTORE_ENTRY:
      return "復旧";
    default:
      return "不明";
  }
};

export const jobTargetLabel = (job: JobSerializers): string => {
  return `[${jobStatusLabel(job.status)}/${jobOperationLabel(job.operation)}] ${
    job.target?.name ?? ""
  }`;
};

export const getLatestCheckDate = (): Date | null => {
  const value = localStorageUtil.get(LocalStorageKey.JobLatestCheckDate);
  return value != null ? new Date(value) : null;
};

export const updateLatestCheckDate = (date: Date) => {
  localStorageUtil.set(LocalStorageKey.JobLatestCheckDate, date.toISOString());
};
