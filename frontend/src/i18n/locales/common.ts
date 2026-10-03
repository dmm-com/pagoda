import { defineMessages } from "../defineMessages";

// Shared vocabulary and messages used across domains.
// Prefer reusing these keys over adding a domain-specific duplicate.
export const commonMessages = defineMessages({
  ja: {
    // Generic actions
    "common.cancel": "キャンセル",
    "common.submit": "送信",
    "common.apply": "適用",
    "common.save": "保存",
    "common.create": "作成",
    "common.update": "更新",
    "common.edit": "編集",
    "common.delete": "削除",
    "common.copy": "コピー",
    "common.restore": "復旧",
    "common.import": "インポート",
    "common.export": "エクスポート",
    "common.download": "ダウンロード",
    "common.details": "詳細",
    "common.close": "閉じる",
    "common.search": "検索",
    "common.name": "名前",
    "common.unknown": "不明",
    "common.backToTop": "トップページへ",

    // Object type names (used as targetName in notifications)
    "common.target.entity": "モデル",
    "common.target.entry": "アイテム",
    "common.target.alias": "エイリアス",
    "common.target.user": "ユーザ",
    "common.target.group": "グループ",
    "common.target.role": "ロール",
    "common.target.category": "カテゴリ",
    "common.target.trigger": "トリガー",

    // Notifications
    "notification.jobRegistered": "{{operationName}}のジョブ登録に成功しました",
    "notification.jobRegistrationFailed":
      "{{operationName}}のジョブ登録に失敗しました",
    "notification.jobCompleted": "{{label}}が完了しました",
    "notification.jobFailed": "{{label}}が失敗しました",
    "notification.jobTimedOut": "{{label}}がタイムアウトしました",
    "notification.operationCompleted":
      "{{targetName}}の{{operationName}}が完了しました。",
    "notification.operationFailed":
      "{{targetName}}の{{operationName}}が失敗しました。",
    "notification.exportReady": "{{targetName}}のエクスポートが完了しました",
    "notification.uploadFailed": "ファイルのアップロードに失敗しました",
    "notification.uploadFailedWithDetail":
      "ファイルのアップロードに失敗しました: {{detail}}",

    // ACL types
    "acl.type.nothing": "権限なし",
    "acl.type.readable": "閲覧",
    "acl.type.writable": "閲覧・編集",
    "acl.type.full": "閲覧・編集・削除",

    // API errors
    "apiError.AE-122000": "入力データが大きすぎます",
    "apiError.AE-210000": "操作に必要な権限が不足しています",
    "apiError.AE-220000": "入力データが既存のデータと重複しています",
    "apiError.AE-240000":
      "紐づくアイテムが残っているため削除できません。先に全てのアイテムを削除してください。",
    "apiError.AE-260000":
      "短期間に同じターゲットに対してインポートが発生しました",

    // Error handler
    "errorHandler.title": "エラーが発生しました",
    "errorHandler.unknownError":
      "不明なエラーが発生しました。トップページに戻って操作し直してください",
    "errorHandler.contactAdmin":
      "エラーが繰り返し発生する場合は管理者にお問い合わせください",
    "errorHandler.detail": "エラー詳細",
    "errorHandler.backToTop": "トップページに戻る",
    "errorHandler.reload": "リロードする",

    // Error pages
    "errorPage.notFound.description":
      "アクセスしたページは削除、変更されたか、現在利用できない可能性があります。",
    "errorPage.forbidden.title": "権限がありません… (|| ﾟДﾟ)",
    "errorPage.forbidden.description1":
      "あなたはこのページを閲覧する権限を持っていません。",
    "errorPage.forbidden.description2":
      "ページの管理者がアクセス権を付与できる可能性があります。",
    "errorPage.unavailable.title": "利用できません:;(∩´﹏`∩);:",
    "errorPage.unavailable.description1":
      "このページは現在、利用ができません。",
    "errorPage.unavailable.description2":
      "管理者からのお知らせをご覧いただくか、お問合せください。",

    // Common components
    "dateRangePicker.startDate": "開始日",
    "dateRangePicker.endDate": "終了日",
    "dateRangePicker.startDateTime": "開始日時",
    "dateRangePicker.endDateTime": "終了日時",
    "dateRangePicker.invalidDateRange": "終了日は開始日以降を指定してください",
    "dateRangePicker.invalidDateTimeRange":
      "終了日時は開始日時以降を指定してください",
    "clipboard.copied": "名前をコピーしました",
    "clipboard.copyName": "名前をコピーする",
    "importForm.permissionDenied": "この操作を行う権限がありません。",
    "importForm.uploadFailed": "ファイルのアップロードに失敗しました。",
    "importForm.checkingChanges": "変更内容を確認しています...",
    "importForm.previewButton": "変更内容を確認",
    "importForm.cancelPreview": "中止",
    "importForm.previewFailed": "変更内容の確認に失敗しました",
    "importForm.loadPageFailed": "変更内容の読み込みに失敗しました",
    "importForm.downloadPreviewFailed": "変更内容のダウンロードに失敗しました",
    "pageHeader.staleData":
      "未処理の変更があります。現在表示されているデータは最新でない可能性があります。",
    "pagination.range": "{{from}} - {{to}} / {{count}} 件",

    // Import preview
    "importPreview.action.create": "新規作成",
    "importPreview.action.update": "更新",
    "importPreview.action.unchanged": "変更なし",
    "importPreview.action.skip": "スキップ",
    "importPreview.action.error": "エラー",
    "importPreview.skipReason.spoofing":
      "作成者が自分ではないため作成できません",
    "importPreview.skipReason.permissionDenied": "更新権限がありません",
    "importPreview.skipReason.disallowUpdate":
      "変更できない項目を変更しようとしています",
    "importPreview.total": "合計 {{count}}",
    "importPreview.filterHintAll": "操作を選ぶと、その行だけを表示します。",
    "importPreview.filterHintSelected":
      "選択中の操作の行だけを表示しています。もう一度押すと解除します。",
    "importPreview.noopMessage":
      "このファイルをインポートしても変更は発生しません。",
    "importPreview.columns.action": "操作",
    "importPreview.columns.kind": "種別",
    "importPreview.columns.name": "名前",
    "importPreview.columns.changes": "変更内容",
    "importPreview.noRows": "表示できる行がありません。",
    "importPreview.loadMore": "さらに読み込む（残り {{remaining}} 行）",
    "importPreview.downloadCsv": "CSV でダウンロード",
    "importPreview.truncatedNotice":
      "行数が多いため一部の行は保持されていません。上のサマリは全 {{total}} 行を集計しています。",
    "importPreview.job.confirmFailed": "変更内容の確認に失敗しました",
    "importPreview.job.confirmTimedOut": "変更内容の確認がタイムアウトしました",
    "importPreview.job.confirmCancelled": "変更内容の確認を中止しました",
  },
  en: {
    // Generic actions
    "common.cancel": "Cancel",
    "common.submit": "Submit",
    "common.apply": "Apply",
    "common.save": "Save",
    "common.create": "Create",
    "common.update": "Update",
    "common.edit": "Edit",
    "common.delete": "Delete",
    "common.copy": "Copy",
    "common.restore": "Restore",
    "common.import": "Import",
    "common.export": "Export",
    "common.download": "Download",
    "common.details": "Details",
    "common.close": "Close",
    "common.search": "Search",
    "common.name": "Name",
    "common.unknown": "Unknown",
    "common.backToTop": "Back to top",

    // Object type names (used as targetName in notifications)
    "common.target.entity": "Entity",
    "common.target.entry": "Entry",
    "common.target.alias": "Alias",
    "common.target.user": "User",
    "common.target.group": "Group",
    "common.target.role": "Role",
    "common.target.category": "Category",
    "common.target.trigger": "Trigger",

    // Notifications
    "notification.jobRegistered":
      "Successfully registered the {{operationName}} job",
    "notification.jobRegistrationFailed":
      "Failed to register the {{operationName}} job",
    "notification.jobCompleted": "{{label}} completed",
    "notification.jobFailed": "{{label}} failed",
    "notification.jobTimedOut": "{{label}} timed out",
    "notification.operationCompleted":
      "{{operationName}} {{targetName}} completed.",
    "notification.operationFailed": "{{operationName}} {{targetName}} failed.",
    "notification.exportReady": "Export of {{targetName}} completed",
    "notification.uploadFailed": "Failed to upload the file",
    "notification.uploadFailedWithDetail":
      "Failed to upload the file: {{detail}}",

    // ACL types
    "acl.type.nothing": "No permission",
    "acl.type.readable": "Read",
    "acl.type.writable": "Read / Write",
    "acl.type.full": "Read / Write / Delete",

    // API errors
    "apiError.AE-122000": "The input data is too large",
    "apiError.AE-210000": "You do not have permission for this operation",
    "apiError.AE-220000": "The input data duplicates existing data",
    "apiError.AE-240000":
      "Cannot delete because linked items still remain. Please delete all items first.",
    "apiError.AE-260000":
      "Another import for the same target was performed a short time ago",

    // Error handler
    "errorHandler.title": "An error occurred",
    "errorHandler.unknownError":
      "An unknown error occurred. Please go back to the top page and try again",
    "errorHandler.contactAdmin":
      "If the error persists, please contact your administrator",
    "errorHandler.detail": "Error details",
    "errorHandler.backToTop": "Back to top page",
    "errorHandler.reload": "Reload",

    // Error pages
    "errorPage.notFound.description":
      "The page you are looking for may have been removed, changed, or is temporarily unavailable.",
    "errorPage.forbidden.title": "Forbidden… (|| ﾟДﾟ)",
    "errorPage.forbidden.description1":
      "You do not have permission to view this page.",
    "errorPage.forbidden.description2":
      "The page administrator may be able to grant you access.",
    "errorPage.unavailable.title": "Unavailable:;(∩´﹏`∩);:",
    "errorPage.unavailable.description1": "This page is currently unavailable.",
    "errorPage.unavailable.description2":
      "Please check announcements from your administrator or contact them.",

    // Common components
    "dateRangePicker.startDate": "Start date",
    "dateRangePicker.endDate": "End date",
    "dateRangePicker.startDateTime": "Start date/time",
    "dateRangePicker.endDateTime": "End date/time",
    "dateRangePicker.invalidDateRange":
      "The end date must be on or after the start date",
    "dateRangePicker.invalidDateTimeRange":
      "The end date/time must be on or after the start date/time",
    "clipboard.copied": "Copied the name",
    "clipboard.copyName": "Copy the name",
    "importForm.permissionDenied":
      "You do not have permission to perform this operation.",
    "importForm.uploadFailed": "Failed to upload the file.",
    "importForm.checkingChanges": "Checking changes...",
    "importForm.previewButton": "Preview changes",
    "importForm.cancelPreview": "Cancel",
    "importForm.previewFailed": "Failed to preview changes",
    "importForm.loadPageFailed": "Failed to load changes",
    "importForm.downloadPreviewFailed": "Failed to download changes",
    "pageHeader.staleData":
      "There are pending changes. The data currently displayed may be out of date.",
    "pagination.range": "{{from}} - {{to}} of {{count}}",

    // Import preview
    "importPreview.action.create": "Create",
    "importPreview.action.update": "Update",
    "importPreview.action.unchanged": "Unchanged",
    "importPreview.action.skip": "Skip",
    "importPreview.action.error": "Error",
    "importPreview.skipReason.spoofing":
      "Cannot create because the creator is not you",
    "importPreview.skipReason.permissionDenied":
      "You do not have permission to update",
    "importPreview.skipReason.disallowUpdate":
      "Attempting to change a field that cannot be changed",
    "importPreview.total": "Total {{count}}",
    "importPreview.filterHintAll":
      "Select an operation to show only those rows.",
    "importPreview.filterHintSelected":
      "Showing only rows for the selected operations. Click again to clear.",
    "importPreview.noopMessage":
      "Importing this file will not cause any changes.",
    "importPreview.columns.action": "Action",
    "importPreview.columns.kind": "Kind",
    "importPreview.columns.name": "Name",
    "importPreview.columns.changes": "Changes",
    "importPreview.noRows": "There are no rows to display.",
    "importPreview.loadMore": "Load more ({{remaining}} rows remaining)",
    "importPreview.downloadCsv": "Download as CSV",
    "importPreview.truncatedNotice":
      "Some rows are not kept because there are too many. The summary above covers all {{total}} rows.",
    "importPreview.job.confirmFailed": "Failed to preview changes",
    "importPreview.job.confirmTimedOut": "Timed out previewing changes",
    "importPreview.job.confirmCancelled": "Cancelled previewing changes",
  },
});
