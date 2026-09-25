import { JobSerializers } from "@dmm-com/airone-apiclient-typescript-fetch";

import { translate } from "../i18n/config";
import {
  LocalStorageKey,
  localStorageUtil,
} from "../repository/LocalStorageUtil";

import { JobOperations, JobStatuses } from "./Constants";

export const jobStatusLabel = (jobStatus: number | undefined): string => {
  switch (jobStatus) {
    case JobStatuses.PREPARING:
      return translate("job.status.preparing");
    case JobStatuses.DONE:
      return translate("job.status.done");
    case JobStatuses.ERROR:
      return translate("job.status.error");
    case JobStatuses.TIMEOUT:
      return translate("job.status.timeout");
    case JobStatuses.PROCESSING:
      return translate("job.status.processing");
    case JobStatuses.CANCELED:
      return translate("job.status.canceled");
    default:
      return translate("job.status.unknown");
  }
};

interface CustomJobOperationType {
  operation: number;
  label: string;
}
let customJobOperations: CustomJobOperationType[] = [];

export const setCustomJobOperations = (
  customCondition: CustomJobOperationType[],
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
      return translate("job.operation.create");
    case JobOperations.EDIT_ENTRY:
    case JobOperations.EDIT_ENTITY:
    case JobOperations.EDIT_ENTITY_V2:
    case JobOperations.EDIT_ENTRY_V2:
      return translate("job.operation.edit");
    case JobOperations.DELETE_ENTITY:
    case JobOperations.DELETE_ENTRY:
    case JobOperations.DELETE_ENTITY_V2:
    case JobOperations.DELETE_ENTRY_V2:
      return translate("job.operation.delete");
    case JobOperations.IMPORT_ENTRY:
    case JobOperations.IMPORT_ENTRY_V2:
      return translate("job.operation.import");
    case JobOperations.EXPORT_ENTRY:
    case JobOperations.EXPORT_SEARCH_RESULT:
    case JobOperations.EXPORT_ENTRY_V2:
    case JobOperations.EXPORT_SEARCH_RESULT_V2:
      return translate("job.operation.export");
    case JobOperations.COPY_ENTRY:
    case JobOperations.DO_COPY_ENTRY:
      return translate("job.operation.copy");
    case JobOperations.RESTORE_ENTRY:
      return translate("job.operation.restore");
    case JobOperations.BULK_EDIT_ENTRY:
      return translate("job.operation.bulkEdit");
    default:
      return translate("job.operation.unknown");
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
