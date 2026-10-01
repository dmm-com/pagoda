import { translate } from "../i18n/config";

export const NotificationMessages = {
  // Job lifecycle
  jobRegistered: (operationName: string) =>
    translate("notification.jobRegistered", { operationName }),
  jobRegistrationFailed: (operationName: string) =>
    translate("notification.jobRegistrationFailed", { operationName }),
  jobCompleted: (label: string) =>
    translate("notification.jobCompleted", { label }),
  jobFailed: (label: string) => translate("notification.jobFailed", { label }),
  jobTimedOut: (label: string) =>
    translate("notification.jobTimedOut", { label }),

  // CRUD operations (used by useFormNotification)
  operationCompleted: (targetName: string, operationName: string) =>
    translate("notification.operationCompleted", {
      targetName,
      operationName,
    }),
  operationFailed: (targetName: string, operationName: string) =>
    translate("notification.operationFailed", { targetName, operationName }),

  // Export
  exportReady: (targetName: string) =>
    translate("notification.exportReady", { targetName }),

  // File
  uploadFailed: (detail?: string) =>
    detail
      ? translate("notification.uploadFailedWithDetail", { detail })
      : translate("notification.uploadFailed"),
} as const;
