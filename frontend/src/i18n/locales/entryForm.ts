import { defineMessages } from "../defineMessages";

export const entryFormMessages = defineMessages({
  ja: {
    // EntryForm
    "entryForm.form.itemName": "アイテム名",
    "entryForm.form.columnItem": "項目",
    "entryForm.form.columnContent": "内容",
    "entryForm.form.required": "必須",

    // Attribute value fields
    "entryForm.dateField.selectDate": "月日を選択",
    "entryForm.dateTimeField.selectDateTime": "日時を選択",
    "entryForm.groupField.selectGroup": "グループを選択",
    "entryForm.roleField.selectRole": "ロールを選択",
    "entryForm.selectField.ariaLabel": "属性 {{attrId}} の選択値",
    "entryForm.selectField.notSelected": "未選択",
    "entryForm.selectField.placeholder": "選択肢を選んでください",
    "entryForm.objectField.selectItem": "アイテムを選択",
    "entryForm.objectField.restrictedItemsNote":
      "（注: 権限によってアイテム表示が制限されています）",
    "entryForm.objectField.disabled": "使用不可",

    // CopyForm
    "entryForm.copyForm.description":
      "入力した各行ごとに {{name}} と同じ属性を持つ別のアイテムを作成",
    "entryForm.copyForm.placeholder": "コピーするアイテム名",
    "entryForm.copyForm.sampleDescription":
      "(Vm0001、vm0002、…vm006の6アイテムを作成する場合)",

    // Zod schema messages
    "entryForm.schema.nameRequired": "アイテム名は必須です",
    "entryForm.schema.nameTooLarge": "アイテム名が大きすぎます",
    "entryForm.schema.invalidChars": "使用できない文字が含まれています",
    "entryForm.schema.valueTooLarge": "属性の値が大きすぎます",
    "entryForm.schema.required": "必須項目です",
    "entryForm.schema.invalidValue": "値が不正です",

    // EntryEditPage / EntryCopyPage
    "entryForm.editPage.leaveConfirm":
      "編集した内容は失われてしまいますが、このページを離れてもよろしいですか？",
    "entryForm.editPage.loading": "読み込み中...",
    "entryForm.editPage.newEntry": "新規作成",
    "entryForm.editPage.editBreadcrumb": "編集",
    "entryForm.editPage.createBreadcrumb": "作成",
    "entryForm.editPage.newEntryTitle": "新規アイテムの作成",
    "entryForm.editPage.editDescription": "アイテム編集",
    "entryForm.editPage.errorDetail": '詳細: "{{message}}"',
    "entryForm.copyPage.description": "アイテムのコピーを作成",
    "entryForm.copyPage.submitName": "コピーを作成",
    "entryForm.copyPage.cannotCopy":
      "アイテム名の登録方法が「利用者が手動で設定」以外の場合はコピーできません",
  },
  en: {
    // EntryForm
    "entryForm.form.itemName": "Entry name",
    "entryForm.form.columnItem": "Item",
    "entryForm.form.columnContent": "Content",
    "entryForm.form.required": "Required",

    // Attribute value fields
    "entryForm.dateField.selectDate": "Select a date",
    "entryForm.dateTimeField.selectDateTime": "Select a date and time",
    "entryForm.groupField.selectGroup": "Select a group",
    "entryForm.roleField.selectRole": "Select a role",
    "entryForm.selectField.ariaLabel":
      "Selection value for attribute {{attrId}}",
    "entryForm.selectField.notSelected": "Not selected",
    "entryForm.selectField.placeholder": "Please select an option",
    "entryForm.objectField.selectItem": "Select an entry",
    "entryForm.objectField.restrictedItemsNote":
      "(Note: Entry display is restricted due to permissions)",
    "entryForm.objectField.disabled": "Disabled",

    // CopyForm
    "entryForm.copyForm.description":
      "Create a new entry with the same attributes as {{name}} for each line entered",
    "entryForm.copyForm.placeholder": "Name of entry to copy",
    "entryForm.copyForm.sampleDescription":
      "(when creating 6 entries such as Vm0001, vm0002, …vm006)",

    // Zod schema messages
    "entryForm.schema.nameRequired": "The entry name is required",
    "entryForm.schema.nameTooLarge": "The entry name is too large",
    "entryForm.schema.invalidChars": "Contains characters that cannot be used",
    "entryForm.schema.valueTooLarge": "The attribute value is too large",
    "entryForm.schema.required": "This field is required",
    "entryForm.schema.invalidValue": "The value is invalid",

    // EntryEditPage / EntryCopyPage
    "entryForm.editPage.leaveConfirm":
      "Your edits will be lost. Are you sure you want to leave this page?",
    "entryForm.editPage.loading": "Loading...",
    "entryForm.editPage.newEntry": "New entry",
    "entryForm.editPage.editBreadcrumb": "Edit",
    "entryForm.editPage.createBreadcrumb": "Create",
    "entryForm.editPage.newEntryTitle": "Create a new entry",
    "entryForm.editPage.editDescription": "Edit entry",
    "entryForm.editPage.errorDetail": 'Detail: "{{message}}"',
    "entryForm.copyPage.description": "Create a copy of the entry",
    "entryForm.copyPage.submitName": "Create copies",
    "entryForm.copyPage.cannotCopy":
      'Copying is not available unless the entry name registration method is set to "Set manually by the user"',
  },
});
