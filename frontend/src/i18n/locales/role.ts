import { defineMessages } from "../defineMessages";

export const roleMessages = defineMessages({
  ja: {
    // RoleForm
    "role.form.columnItem": "項目",
    "role.form.columnContent": "内容",
    "role.form.name": "ロール名",
    "role.form.namePlaceholder": "ロール名",
    "role.form.description": "備考",
    "role.form.descriptionPlaceholder": "備考",
    "role.form.registerSectionTitle": "ユーザ/グループを登録",
    "role.form.registerSectionHelp":
      "ロール管理するグループまたはユーザを登録してください。",
    "role.form.groupRegisterTitle": "グループ登録",
    "role.form.userRegisterTitle": "ユーザ登録",
    "role.form.admin": "管理者",
    "role.form.member": "メンバー",
    "role.form.nameRequired": "ロール名は必須です",
    "role.form.adminRequired":
      "管理者ユーザーか管理者グループのどちらかは必ずメンバーを指定してください",
    "role.form.userDuplicateWithAdmin":
      "管理者と重複しているユーザーがあります",
    "role.form.groupDuplicateWithAdmin":
      "管理者と重複しているグループがあります",
    "role.form.memberDuplicateUser": "メンバーとユーザーが重複しています",
    "role.form.memberDuplicateGroup": "メンバーとグループが重複しています",

    // RoleImportModal
    "role.importModal.title": "ロールのインポート",
    "role.importModal.description":
      "インポートするファイルを選択してください。",
    "role.importModal.caption": "※CSV形式のファイルは選択できません。",
    "role.importModal.accepted": "ロールのインポートを受け付けました。",

    // RoleList
    "role.list.roleColumn": "ロール",
    "role.list.descriptionColumn": "備考",
    "role.list.membersColumn": "登録ユーザ・グループ",
    "role.list.deleteColumn": "削除",
    "role.list.editColumn": "編集",
    "role.list.adminBadge": "管理者",
    "role.list.deleteConfirm": "本当に削除しますか？",
    "role.list.deleteSuccess": "ロールの削除が完了しました",
    "role.list.deleteFailure": "ロールの削除が失敗しました",
    "role.list.deleteAriaLabel": "{{name}}を削除",
    "role.list.editAriaLabel": "{{name}}を編集",

    // RoleListPage
    "role.listPage.pageTitle": "ロール管理",
    "role.listPage.createNew": "新規ロールを作成",

    // RoleEditPage
    "role.edit.breadcrumb": "ロール編集",
    "role.edit.pageTitleNew": "新規ロールの作成",
    "role.edit.description": "ロール編集",
    "role.edit.confirmLeave":
      "編集した内容は失われてしまいますが、このページを離れてもよろしいですか？",
    "role.edit.loading": "読み込み中...",
    "role.edit.newRolePrefix": "新規作成",
    "role.edit.submitFailureDetail": '詳細: "{{message}}"',
  },
  en: {
    // RoleForm
    "role.form.columnItem": "Item",
    "role.form.columnContent": "Content",
    "role.form.name": "Role name",
    "role.form.namePlaceholder": "Role name",
    "role.form.description": "Notes",
    "role.form.descriptionPlaceholder": "Notes",
    "role.form.registerSectionTitle": "Register users/groups",
    "role.form.registerSectionHelp":
      "Please register the groups or users to be managed by this role.",
    "role.form.groupRegisterTitle": "Register groups",
    "role.form.userRegisterTitle": "Register users",
    "role.form.admin": "Admin",
    "role.form.member": "Member",
    "role.form.nameRequired": "Role name is required",
    "role.form.adminRequired":
      "You must specify at least one member in either the admin users or admin groups",
    "role.form.userDuplicateWithAdmin":
      "There are users that overlap with the admins",
    "role.form.groupDuplicateWithAdmin":
      "There are groups that overlap with the admins",
    "role.form.memberDuplicateUser":
      "There are members that overlap with the users",
    "role.form.memberDuplicateGroup":
      "There are members that overlap with the groups",

    // RoleImportModal
    "role.importModal.title": "Import roles",
    "role.importModal.description": "Please select a file to import.",
    "role.importModal.caption": "* CSV files cannot be selected.",
    "role.importModal.accepted": "The role import has been accepted.",

    // RoleList
    "role.list.roleColumn": "Role",
    "role.list.descriptionColumn": "Notes",
    "role.list.membersColumn": "Registered users/groups",
    "role.list.deleteColumn": "Delete",
    "role.list.editColumn": "Edit",
    "role.list.adminBadge": "Admin",
    "role.list.deleteConfirm": "Are you sure you want to delete this?",
    "role.list.deleteSuccess": "Successfully deleted the role",
    "role.list.deleteFailure": "Failed to delete the role",
    "role.list.deleteAriaLabel": "Delete {{name}}",
    "role.list.editAriaLabel": "Edit {{name}}",

    // RoleListPage
    "role.listPage.pageTitle": "Role management",
    "role.listPage.createNew": "Create a new role",

    // RoleEditPage
    "role.edit.breadcrumb": "Edit role",
    "role.edit.pageTitleNew": "Create a new role",
    "role.edit.description": "Edit role",
    "role.edit.confirmLeave":
      "Your edits will be lost. Are you sure you want to leave this page?",
    "role.edit.loading": "Loading...",
    "role.edit.newRolePrefix": "New",
    "role.edit.submitFailureDetail": 'Details: "{{message}}"',
  },
});
