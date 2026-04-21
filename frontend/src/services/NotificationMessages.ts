export const NotificationMessages = {
  // Job lifecycle
  jobRegistered: (operationName: string) =>
    `${operationName}のジョブ登録に成功しました`,
  jobRegistrationFailed: (operationName: string) =>
    `${operationName}のジョブ登録に失敗しました`,
  jobCompleted: (label: string) => `${label}が完了しました`,
  jobFailed: (label: string) => `${label}が失敗しました`,
  jobTimedOut: (label: string) => `${label}がタイムアウトしました`,

  // CRUD operations (used by useFormNotification)
  operationCompleted: (targetName: string, operationName: string) =>
    `${targetName}の${operationName}が完了しました。`,
  operationFailed: (targetName: string, operationName: string) =>
    `${targetName}の${operationName}が失敗しました。`,

  // Export
  exportReady: (targetName: string) =>
    `${targetName}のエクスポートが完了しました`,

  // File
  uploadFailed: (detail?: string) =>
    `ファイルのアップロードに失敗しました${detail ? `: ${detail}` : ""}`,
} as const;
