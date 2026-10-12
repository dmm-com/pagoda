import { defineMessages } from "../defineMessages";

export const entryMessages = defineMessages({
  ja: {
    // Shared table headers / labels
    "entry.common.itemHeader": "項目",
    "entry.common.valueHeader": "内容",
    "entry.common.changeHistory": "変更履歴",

    // AliasEntryList
    "entry.alias.addPlaceholder": "エイリアスを追加",

    // AliasEntryListPage / ListAliasEntryPage
    "entry.alias.settingsTitle": "エイリアス設定",
    "entry.alias.deleteSuccess": "エイリアスの削除が完了しました。",
    "entry.alias.deleteFailure": "エイリアスの削除が失敗しました。",
    "entry.alias.detailMessage": '詳細: "{{message}}"',

    // AttrStatsModal
    "entry.attrStats.title": "「{{attrname}}」の集計",
    "entry.attrStats.blank": "(空白)",
    "entry.attrStats.progress": "{{displayedCount}} / {{totalCount}} 件",
    "entry.attrStats.valueHeader": "値",
    "entry.attrStats.countHeader": "件数",
    "entry.attrStats.loadFailed": "集計に失敗しました",

    // EntryAttributes
    "entry.attributes.triggerTooltip":
      "この属性には Trigger が設定されています",
    "entry.attributes.noteAriaLabel": "{{name}}の説明",

    // EntryBreadcrumbs
    "entry.breadcrumbs.entityList": "モデル一覧",

    // EntryControlMenu
    "entry.control.deleteSuccess": "アイテムの削除が完了しました",
    "entry.control.deleteFailure": "アイテムの削除が失敗しました",
    "entry.control.aclSettings": "ACL 設定",
    "entry.control.aclChangeHistory": "ACL 変更履歴",
    "entry.control.confirmDelete": "本当に削除しますか？",

    // EntryHistoryList
    "entry.history.beforeHeader": "変更前",
    "entry.history.afterHeader": "変更後",
    "entry.history.executedAtHeader": "実行日時",
    "entry.history.executedByHeader": "実行者",
    "entry.history.restoreSuccess": "変更の復旧が完了しました",
    "entry.history.restoreFailure": "変更の復旧が失敗しました",
    "entry.history.confirmRestoreValue": "変更前の値に復旧しますか？",

    // EntryImportModal
    "entry.import.title": "アイテムのインポート",
    "entry.import.description": "インポートするファイルを選択してください。",
    "entry.import.caption": "※CSV形式のファイルは選択できません。",
    "entry.import.forceLabel":
      "強制的にインポートする(短期間にインポートを繰り返したい場合に使用してください)",

    // EntryList
    "entry.list.searchPlaceholder": "アイテムを絞り込む",
    "entry.list.createButton": "新規アイテムを作成",

    // EntryListCard
    "entry.listCard.operationsTooltip": "アイテムの操作",

    // EntryReferral
    "entry.referral.countLabel": "関連づけられたアイテム(計{{count}})",

    // EntrySelfHistoryList
    "entry.selfHistory.restoreSuccess": "アイテム名の復旧が完了しました",
    "entry.selfHistory.restoreFailure": "アイテム名の復旧が失敗しました",
    "entry.selfHistory.operationHeader": "操作",
    "entry.selfHistory.beforeNameHeader": "変更前のアイテム名",
    "entry.selfHistory.afterNameHeader": "変更後のアイテム名",
    "entry.selfHistory.confirmRestore":
      "アイテム名を「{{name}}」に復旧しますか？",

    // RestorableEntryList
    "entry.restorable.confirmRestore": "本当に復旧しますか？",
    "entry.restorable.restoreSuccess": "アイテムの復旧が完了しました",
    "entry.restorable.restoreFailure": "アイテムの復旧が失敗しました",

    // EntryDetailsPage
    "entry.details.pageDescription": "アイテム詳細",
    "entry.details.attrListLabel": "項目一覧",

    // EntryListPage
    "entry.listPage.description": "アイテム一覧",

    // EntryHistoryListPage
    "entry.historyPage.selfHistorySection": "アイテム変更履歴",
    "entry.historyPage.attrHistorySection": "属性変更履歴",

    // EntryRestorePage
    "entry.restorePage.description": "削除アイテムの復旧",

    // ExternalLinkConfirmDialog
    "entry.externalLink.confirmTitle": "外部サイトを開きますか？",
  },
  en: {
    // Shared table headers / labels
    "entry.common.itemHeader": "Item",
    "entry.common.valueHeader": "Value",
    "entry.common.changeHistory": "Change History",

    // AliasEntryList
    "entry.alias.addPlaceholder": "Add alias",

    // AliasEntryListPage / ListAliasEntryPage
    "entry.alias.settingsTitle": "Alias settings",
    "entry.alias.deleteSuccess": "Successfully deleted the alias.",
    "entry.alias.deleteFailure": "Failed to delete the alias.",
    "entry.alias.detailMessage": 'Details: "{{message}}"',

    // AttrStatsModal
    "entry.attrStats.title": "Aggregation of “{{attrname}}”",
    "entry.attrStats.blank": "(blank)",
    "entry.attrStats.progress": "{{displayedCount}} / {{totalCount}}",
    "entry.attrStats.valueHeader": "Value",
    "entry.attrStats.countHeader": "Count",
    "entry.attrStats.loadFailed": "Failed to aggregate",

    // EntryAttributes
    "entry.attributes.triggerTooltip":
      "A trigger is configured for this attribute",
    "entry.attributes.noteAriaLabel": "Description of {{name}}",

    // EntryBreadcrumbs
    "entry.breadcrumbs.entityList": "Entity list",

    // EntryControlMenu
    "entry.control.deleteSuccess": "Successfully deleted the entry",
    "entry.control.deleteFailure": "Failed to delete the entry",
    "entry.control.aclSettings": "ACL settings",
    "entry.control.aclChangeHistory": "ACL change history",
    "entry.control.confirmDelete": "Are you sure you want to delete this?",

    // EntryHistoryList
    "entry.history.beforeHeader": "Before change",
    "entry.history.afterHeader": "After change",
    "entry.history.executedAtHeader": "Executed at",
    "entry.history.executedByHeader": "Executed by",
    "entry.history.restoreSuccess": "Successfully restored the change",
    "entry.history.restoreFailure": "Failed to restore the change",
    "entry.history.confirmRestoreValue":
      "Are you sure you want to restore the previous value?",

    // EntryImportModal
    "entry.import.title": "Import entries",
    "entry.import.description": "Please select a file to import.",
    "entry.import.caption": "* Files in CSV format cannot be selected.",
    "entry.import.forceLabel":
      "Force import (use this if you need to repeat an import in a short period of time)",

    // EntryList
    "entry.list.searchPlaceholder": "Filter entries",
    "entry.list.createButton": "Create new entry",

    // EntryListCard
    "entry.listCard.operationsTooltip": "Entry operations",

    // EntryReferral
    "entry.referral.countLabel": "Referring entries (total {{count}})",

    // EntrySelfHistoryList
    "entry.selfHistory.restoreSuccess": "Successfully restored the entry name",
    "entry.selfHistory.restoreFailure": "Failed to restore the entry name",
    "entry.selfHistory.operationHeader": "Operation",
    "entry.selfHistory.beforeNameHeader": "Entry name before change",
    "entry.selfHistory.afterNameHeader": "Entry name after change",
    "entry.selfHistory.confirmRestore":
      'Are you sure you want to restore the entry name to "{{name}}"?',

    // RestorableEntryList
    "entry.restorable.confirmRestore": "Are you sure you want to restore this?",
    "entry.restorable.restoreSuccess": "Successfully restored the entry",
    "entry.restorable.restoreFailure": "Failed to restore the entry",

    // EntryDetailsPage
    "entry.details.pageDescription": "Entry details",
    "entry.details.attrListLabel": "Attribute list",

    // EntryListPage
    "entry.listPage.description": "Entry list",

    // EntryHistoryListPage
    "entry.historyPage.selfHistorySection": "Entry change history",
    "entry.historyPage.attrHistorySection": "Attribute change history",

    // EntryRestorePage
    "entry.restorePage.description": "Restore deleted entries",

    // ExternalLinkConfirmDialog
    "entry.externalLink.confirmTitle":
      "Are you sure you want to open the external site?",
  },
});
