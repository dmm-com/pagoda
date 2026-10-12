import { defineMessages } from "../defineMessages";

export const groupMessages = defineMessages({
  ja: {
    // GroupControlMenu
    "group.controlMenu.editGroup": "グループ編集",
    "group.controlMenu.deleteConfirm": "本当に削除しますか？",
    "group.controlMenu.deleteSuccess": "グループの削除が完了しました",
    "group.controlMenu.deleteFailure": "グループの削除が失敗しました",

    // GroupForm
    "group.form.columnItem": "項目",
    "group.form.columnContent": "内容",
    "group.form.name": "グループ名",
    "group.form.namePlaceholder": "グループ名",
    "group.form.members": "登録ユーザ",
    "group.form.parentGroupSectionTitle": "所属グループ",
    "group.form.parentGroupHelp":
      "直下となるグループにチェックマークを入れてください。独立グループの場合は未選択のまま保存してください。",
    "group.form.nameRequired": "グループ名は必須です",

    // GroupImportModal
    "group.importModal.title": "グループのインポート",
    "group.importModal.description":
      "インポートするファイルを選択してください。",
    "group.importModal.caption": "※CSV形式のファイルは選択できません。",

    // GroupListPage
    "group.list.pageTitle": "グループ管理",
    "group.list.selectHelp":
      "選択したいグループにチェックマークを入れてください。",
    "group.list.memberCount": "属するユーザ(計 {{count}})",
    "group.list.searchPlaceholder": "ユーザを絞り込む",
    "group.list.createNew": "新規グループを作成",

    // GroupEditPage
    "group.edit.breadcrumbCreate": "新規グループの作成",
    "group.edit.breadcrumbEdit": "グループの編集",
    "group.edit.pageTitleNew": "新規グループの作成",
    "group.edit.description": "グループ編集",
    "group.edit.confirmLeave":
      "編集した内容は失われてしまいますが、このページを離れてもよろしいですか？",
    "group.edit.loading": "読み込み中...",
    "group.edit.newGroupPrefix": "新規作成",
    "group.edit.submitFailureDetail": '詳細: "{{message}}"',
  },
  en: {
    // GroupControlMenu
    "group.controlMenu.editGroup": "Edit group",
    "group.controlMenu.deleteConfirm": "Are you sure you want to delete this?",
    "group.controlMenu.deleteSuccess": "Successfully deleted the group",
    "group.controlMenu.deleteFailure": "Failed to delete the group",

    // GroupForm
    "group.form.columnItem": "Item",
    "group.form.columnContent": "Content",
    "group.form.name": "Group name",
    "group.form.namePlaceholder": "Group name",
    "group.form.members": "Registered users",
    "group.form.parentGroupSectionTitle": "Parent group",
    "group.form.parentGroupHelp":
      "Please check the group that this will be a direct child of. If this is an independent group, save it without selecting one.",
    "group.form.nameRequired": "Group name is required",

    // GroupImportModal
    "group.importModal.title": "Import groups",
    "group.importModal.description": "Please select a file to import.",
    "group.importModal.caption": "* CSV files cannot be selected.",

    // GroupListPage
    "group.list.pageTitle": "Group management",
    "group.list.selectHelp": "Please check the group you want to select.",
    "group.list.memberCount": "Members ({{count}} total)",
    "group.list.searchPlaceholder": "Filter users",
    "group.list.createNew": "Create a new group",

    // GroupEditPage
    "group.edit.breadcrumbCreate": "Create a new group",
    "group.edit.breadcrumbEdit": "Edit group",
    "group.edit.pageTitleNew": "Create a new group",
    "group.edit.description": "Edit group",
    "group.edit.confirmLeave":
      "Your edits will be lost. Are you sure you want to leave this page?",
    "group.edit.loading": "Loading...",
    "group.edit.newGroupPrefix": "New",
    "group.edit.submitFailureDetail": 'Details: "{{message}}"',
  },
});
