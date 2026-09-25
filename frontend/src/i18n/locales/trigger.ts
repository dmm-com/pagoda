import { defineMessages } from "../defineMessages";

export const triggerMessages = defineMessages({
  ja: {
    // TriggerFormSchema
    "trigger.form.entityRequired": "モデルは必須です",
    "trigger.form.attrRequired": "属性は必須です",
    "trigger.form.conditionsRequired": "最低でもひとつの条件を設定してください",
    "trigger.form.actionsRequired":
      "最低でもひとつのアクションを設定してください",
    "trigger.form.confirmLeave":
      "編集した内容は失われてしまいますが、このページを離れてもよろしいですか？",

    // TriggerListPage
    "trigger.list.title": "トリガー管理",
    "trigger.list.createButton": "新規トリガーを作成",
    "trigger.list.confirmDelete": "本当に削除しますか？",
    "trigger.list.deleteSuccess": "トリガーの削除が完了しました",
    "trigger.list.deleteFailed": "トリガーの削除が失敗しました",
    "trigger.list.columnModel": "モデル",
    "trigger.list.columnCondition": "条件",
    "trigger.list.columnAction": "アクション",

    // TriggerEditPage
    "trigger.edit.createTitle": "新規トリガーの作成",
    "trigger.edit.editTitle": "トリガー編集",
    "trigger.edit.targetEntity": "設定対象のモデル",
    "trigger.edit.entityPlaceholder": "モデルを選択",
    "trigger.edit.conditionsHeading": "条件",
    "trigger.edit.actionsHeading": "アクション",
    "trigger.edit.columnAttrName": "属性名",
    "trigger.edit.columnValue": "値",
    "trigger.edit.columnAdd": "追加",
  },
  en: {
    // TriggerFormSchema
    "trigger.form.entityRequired": "Model is required",
    "trigger.form.attrRequired": "Attribute is required",
    "trigger.form.conditionsRequired": "Set at least one condition",
    "trigger.form.actionsRequired": "Set at least one action",
    "trigger.form.confirmLeave":
      "Any changes you made will be lost. Are you sure you want to leave this page?",

    // TriggerListPage
    "trigger.list.title": "Trigger management",
    "trigger.list.createButton": "Create new trigger",
    "trigger.list.confirmDelete": "Are you sure you want to delete this?",
    "trigger.list.deleteSuccess": "Successfully deleted the trigger",
    "trigger.list.deleteFailed": "Failed to delete the trigger",
    "trigger.list.columnModel": "Model",
    "trigger.list.columnCondition": "Condition",
    "trigger.list.columnAction": "Action",

    // TriggerEditPage
    "trigger.edit.createTitle": "Create a new trigger",
    "trigger.edit.editTitle": "Edit trigger",
    "trigger.edit.targetEntity": "Target model",
    "trigger.edit.entityPlaceholder": "Select a model",
    "trigger.edit.conditionsHeading": "Conditions",
    "trigger.edit.actionsHeading": "Actions",
    "trigger.edit.columnAttrName": "Attribute name",
    "trigger.edit.columnValue": "Value",
    "trigger.edit.columnAdd": "Add",
  },
});
