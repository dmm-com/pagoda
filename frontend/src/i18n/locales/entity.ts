import { defineMessages } from "../defineMessages";

export const entityMessages = defineMessages({
  ja: {
    // Entity list
    "entity.list.pageTitle": "モデル一覧",
    "entity.list.searchPlaceholder": "モデルを絞り込む",
    "entity.list.createButton": "新規モデルを作成",
    "entity.list.actionsTooltip": "モデルの操作",

    // Entity control menu
    "entity.controlMenu.entryList": "アイテム一覧",
    "entity.controlMenu.aliasList": "エイリアス一覧",
    "entity.controlMenu.aclSettings": "ACL 設定",
    "entity.controlMenu.history": "変更履歴",
    "entity.controlMenu.aclHistory": "ACL 変更履歴",
    "entity.controlMenu.exportFormat": "エクスポート({{format}})",
    "entity.controlMenu.restoreEntries": "削除アイテムの復旧",
    "entity.controlMenu.deleteConfirm": "本当に削除しますか？",
    "entity.controlMenu.deleteSucceeded": "モデルの削除が完了しました",
    "entity.controlMenu.deleteFailed": "モデルの削除が失敗しました",
    "entity.controlMenu.deleteFailedWithDetail":
      "モデルの削除が失敗しました: {{detail}}",

    // Entity form: basic fields
    "entity.form.basicInfoTitle": "基本情報",
    "entity.form.itemHeader": "項目",
    "entity.form.valueHeader": "内容",
    "entity.form.nameLabel": "モデル名",
    "entity.form.noteLabel": "備考",
    "entity.form.itemNameTypeLabel": "アイテム名の登録方法",
    "entity.form.itemNameTypeUser": "利用者が手動で設定",
    "entity.form.itemNameTypeUuid": "UUIDに自動で設定",
    "entity.form.itemNameTypeAttr": "属性値に応じて自動で設定",
    "entity.form.autoNameEmptyPreview":
      "（自動命名が設定された属性がありません）",
    "entity.form.itemNamePatternLabel": "アイテム名の許可パターン",
    "entity.form.showOnTopPage": "トップページに表示",
    "entity.form.deleteChainExcludeLabel": "関連削除の判定から除外するモデル",
    "entity.form.selectEntityPlaceholder": "モデルを選択",
    "entity.form.dragReorderTooltip": "ドラッグして並び替え",
    "entity.form.dragReorderAriaLabel":
      "{{index}} 番目の属性をドラッグして並び替え",
    "entity.form.unnamedAttribute": "未命名属性",
    "entity.form.attrTypeAriaLabel": "{{name}}の属性型",
    "entity.form.selectEntityFirstOption": "参照先モデルを先に選択",
    "entity.form.noMatchingAttrOption": "該当する属性がありません",
    "entity.form.displayAttrPlaceholder": "表示ラベルに使う属性名 (任意)",
    "entity.form.defaultValueAriaLabel": "{{index}} 番目の属性のデフォルト値",
    "entity.form.deleteAttrAriaLabel": "{{index}} 番目の属性を削除",
    "entity.form.appendAttrAriaLabel": "{{index}} 番目の後に属性を追加",
    "entity.form.attrMenuAriaLabel": "{{index}} 番目の属性の詳細メニューを開く",
    "entity.form.mandatoryAriaLabel": "{{index}} 番目の属性を必須にする",
    "entity.form.deleteInChainAriaLabel":
      "{{index}} 番目の属性を関連削除に連動する",
    "entity.form.addAttrAriaLabel": "属性を追加",

    // Entity form: attribute fields
    "entity.form.attributesTitle": "属性情報",
    "entity.form.attrNameHeader": "属性名",
    "entity.form.attrTypeHeader": "型",
    "entity.form.defaultValueHeader": "デフォルト値",
    "entity.form.reorderHeader": "並び替え",
    "entity.form.addHeader": "追加",
    "entity.form.defaultValueUnsupported": "この型では未サポート",
    "entity.form.attrDescriptionMenuTitle": "属性説明",
    "entity.form.attrDescriptionMenuSubtitle": "属性の説明文を設定",
    "entity.form.autoNameMenuTitle": "自動命名",
    "entity.form.autoNameMenuSubtitle": "属性値からアイテム名を自動設定",
    "entity.form.aclMenuTitle": "ACL設定",
    "entity.form.aclMenuSubtitle": "属性の権限を設定",
    "entity.form.mandatoryMenuTitle": "必須設定",
    "entity.form.mandatoryMenuSubtitle": "属性値の設定を必須化",
    "entity.form.deleteInChainMenuTitle": "関連削除",
    "entity.form.deleteInChainMenuSubtitle": "参照アイテムの削除に連動",

    // Entity form: auto name config modal
    "entity.form.autoNameConfigTitle": "アイテム名の自動設定",
    "entity.form.autoNameConfigCaption":
      "属性値からアイテム名を自動的に登録するための設定",
    "entity.form.nameOrderLabel": "名前に設定する順番",
    "entity.form.namePrefixLabel": "名前に付ける接頭辞",
    "entity.form.namePostfixLabel": "名前に付ける接尾辞",

    // Entity form: attribute note modal
    "entity.form.attrNoteModalCaption": "必要に応じてご入力ください",
    "entity.form.attrNotePlaceholder": "説明",

    // Entity form: webhook fields
    "entity.form.webhookLabel": "ラベル",
    "entity.form.webhookEnabledHeader": "有効",
    "entity.form.webhookVerificationError":
      "エラーのため webhook が有効になっていません。詳細: {{detail}}",
    "entity.form.webhookHeadersCaption":
      "指定した endpoint URL に送るリクエストに付加するヘッダ情報を入力してください。",

    // Entity form: isolation rules fields
    "entity.form.isolationTitle": "他アイテムから参照されなくなる設定",
    "entity.form.isolationTargetEntityHeader": "対象モデル",
    "entity.form.isolationAllEntitiesHeader": "全モデル",
    "entity.form.isolationAttrHeader": "属性",
    "entity.form.isolationExcludeValueHeader": "除外するアイテムの属性値",
    "entity.form.isolationSelectAttrPlaceholder": "属性を選択",
    "entity.form.isolationNamePlaceholder": "名前",
    "entity.form.isolationValuePlaceholder": "値",

    // Entity form: validation
    "entity.form.validation.nameRequired": "モデル名は必須です",
    "entity.form.validation.invalidRegex":
      "正規表現として正しい文字列を入力してください",
    "entity.form.validation.conditionsRequired": "条件は1つ以上必要です",
    "entity.form.validation.urlRequired": "URLは必須です",
    "entity.form.validation.invalidUrl":
      "URLとして正しい文字列を入力してください",
    "entity.form.validation.headerKeyRequired": "ヘッダキーは必須です",
    "entity.form.validation.attrNameRequired": "属性名は必須です",
    "entity.form.validation.referralRequired":
      "オブジェクト型を選択した場合、参照先は必須です",
    "entity.form.validation.duplicateAttrName": "属性名が重複しています",
    "entity.form.validation.choiceLabelRequired": "選択肢の表示名は必須です",
    "entity.form.validation.choicesRequired":
      "選択肢型を選択した場合、選択肢は1つ以上必要です",
    "entity.form.validation.choiceLabelUnique":
      "選択肢の表示名は重複できません",
    "entity.form.choicesLabel": "選択肢",
    "entity.form.choiceDisplayNamePlaceholder": "選択肢の表示名",
    "entity.form.choiceInUseTooltip":
      "この選択肢は既存のアイテムで使用中のため削除できません",
    "entity.form.addChoiceButton": "選択肢を追加",
    "entity.form.defaultObjectValuePlaceholder": "デフォルトのアイテム",

    // Entity history
    "entity.history.contentHeader": "内容",
    "entity.history.beforeHeader": "変更前",
    "entity.history.afterHeader": "変更後",
    "entity.history.executedAtHeader": "実行日時",
    "entity.history.executedByHeader": "実行者",
    "entity.history.opCreate": "作成",
    "entity.history.opModify": "変更",
    "entity.history.opAddAttr": "属性追加",
    "entity.history.opModAttr": "属性変更",
    "entity.history.opDelAttr": "属性削除",

    // Entity import modal
    "entity.import.title": "モデルのインポート",
    "entity.import.description": "インポートするファイルを選択してください。",
    "entity.import.caption": "※CSV形式のファイルは選択できません。",

    // Entity edit page
    "entity.edit.leaveConfirm":
      "編集した内容は失われてしまいますが、このページを離れてもよろしいですか？",
    "entity.edit.errorDetail": '詳細: "{{message}}"',
    "entity.edit.loading": "読み込み中...",
    "entity.edit.newTitlePrefix": "新規作成",
    "entity.edit.newEntityTitle": "新規モデルの作成",
    "entity.edit.description": "エンティテイティ詳細 / 編集",
  },
  en: {
    // Entity list
    "entity.list.pageTitle": "Entities",
    "entity.list.searchPlaceholder": "Filter entities",
    "entity.list.createButton": "Create entity",
    "entity.list.actionsTooltip": "Entity actions",

    // Entity control menu
    "entity.controlMenu.entryList": "Entries",
    "entity.controlMenu.aliasList": "Aliases",
    "entity.controlMenu.aclSettings": "ACL settings",
    "entity.controlMenu.history": "Change history",
    "entity.controlMenu.aclHistory": "ACL change history",
    "entity.controlMenu.exportFormat": "Export ({{format}})",
    "entity.controlMenu.restoreEntries": "Restore deleted entries",
    "entity.controlMenu.deleteConfirm": "Are you sure you want to delete this?",
    "entity.controlMenu.deleteSucceeded": "Successfully deleted the entity",
    "entity.controlMenu.deleteFailed": "Failed to delete the entity",
    "entity.controlMenu.deleteFailedWithDetail":
      "Failed to delete the entity: {{detail}}",

    // Entity form: basic fields
    "entity.form.basicInfoTitle": "Basic information",
    "entity.form.itemHeader": "Item",
    "entity.form.valueHeader": "Value",
    "entity.form.nameLabel": "Entity name",
    "entity.form.noteLabel": "Notes",
    "entity.form.itemNameTypeLabel": "Item name assignment method",
    "entity.form.itemNameTypeUser": "Set manually by user",
    "entity.form.itemNameTypeUuid": "Auto-set to UUID",
    "entity.form.itemNameTypeAttr": "Auto-set based on attribute values",
    "entity.form.autoNameEmptyPreview":
      "(No attributes configured for auto-naming)",
    "entity.form.itemNamePatternLabel": "Allowed item name pattern",
    "entity.form.showOnTopPage": "Show on top page",
    "entity.form.deleteChainExcludeLabel":
      "Entities excluded from cascade delete",
    "entity.form.selectEntityPlaceholder": "Select an entity",
    "entity.form.dragReorderTooltip": "Drag to reorder",
    "entity.form.dragReorderAriaLabel": "Drag to reorder attribute {{index}}",
    "entity.form.unnamedAttribute": "Unnamed attribute",
    "entity.form.attrTypeAriaLabel": "Type of {{name}}",
    "entity.form.selectEntityFirstOption": "Select a referral entity first",
    "entity.form.noMatchingAttrOption": "No matching attributes",
    "entity.form.displayAttrPlaceholder":
      "Attribute name for the display label (optional)",
    "entity.form.defaultValueAriaLabel": "Default value of attribute {{index}}",
    "entity.form.deleteAttrAriaLabel": "Delete attribute {{index}}",
    "entity.form.appendAttrAriaLabel": "Add attribute after {{index}}",
    "entity.form.attrMenuAriaLabel": "Open detail menu of attribute {{index}}",
    "entity.form.mandatoryAriaLabel": "Make attribute {{index}} mandatory",
    "entity.form.deleteInChainAriaLabel":
      "Link attribute {{index}} to related deletion",
    "entity.form.addAttrAriaLabel": "Add attribute",

    // Entity form: attribute fields
    "entity.form.attributesTitle": "Attribute information",
    "entity.form.attrNameHeader": "Attribute name",
    "entity.form.attrTypeHeader": "Type",
    "entity.form.defaultValueHeader": "Default value",
    "entity.form.reorderHeader": "Reorder",
    "entity.form.addHeader": "Add",
    "entity.form.defaultValueUnsupported": "Not supported for this type",
    "entity.form.attrDescriptionMenuTitle": "Attribute description",
    "entity.form.attrDescriptionMenuSubtitle":
      "Set a description for the attribute",
    "entity.form.autoNameMenuTitle": "Auto naming",
    "entity.form.autoNameMenuSubtitle":
      "Auto-set the item name from attribute values",
    "entity.form.aclMenuTitle": "ACL settings",
    "entity.form.aclMenuSubtitle": "Set permissions for the attribute",
    "entity.form.mandatoryMenuTitle": "Required",
    "entity.form.mandatoryMenuSubtitle": "Require a value for this attribute",
    "entity.form.deleteInChainMenuTitle": "Cascade delete",
    "entity.form.deleteInChainMenuSubtitle":
      "Delete when the referenced entry is deleted",

    // Entity form: auto name config modal
    "entity.form.autoNameConfigTitle": "Automatic item naming",
    "entity.form.autoNameConfigCaption":
      "Configure automatic item naming from attribute values",
    "entity.form.nameOrderLabel": "Order in the name",
    "entity.form.namePrefixLabel": "Name prefix",
    "entity.form.namePostfixLabel": "Name suffix",

    // Entity form: attribute note modal
    "entity.form.attrNoteModalCaption": "Enter if necessary",
    "entity.form.attrNotePlaceholder": "Description",

    // Entity form: webhook fields
    "entity.form.webhookLabel": "Label",
    "entity.form.webhookEnabledHeader": "Enabled",
    "entity.form.webhookVerificationError":
      "The webhook is not enabled due to an error. Details: {{detail}}",
    "entity.form.webhookHeadersCaption":
      "Enter header information to add to requests sent to the specified endpoint URL.",

    // Entity form: isolation rules fields
    "entity.form.isolationTitle":
      "Settings for entries no longer referenced by other entries",
    "entity.form.isolationTargetEntityHeader": "Target entity",
    "entity.form.isolationAllEntitiesHeader": "All entities",
    "entity.form.isolationAttrHeader": "Attribute",
    "entity.form.isolationExcludeValueHeader":
      "Attribute value of excluded entries",
    "entity.form.isolationSelectAttrPlaceholder": "Select an attribute",
    "entity.form.isolationNamePlaceholder": "Name",
    "entity.form.isolationValuePlaceholder": "Value",

    // Entity form: validation
    "entity.form.validation.nameRequired": "Entity name is required",
    "entity.form.validation.invalidRegex":
      "Please enter a valid regular expression",
    "entity.form.validation.conditionsRequired":
      "At least one condition is required",
    "entity.form.validation.urlRequired": "URL is required",
    "entity.form.validation.invalidUrl": "Please enter a valid URL",
    "entity.form.validation.headerKeyRequired": "Header key is required",
    "entity.form.validation.attrNameRequired": "Attribute name is required",
    "entity.form.validation.referralRequired":
      "A referral is required when an object type is selected",
    "entity.form.validation.duplicateAttrName": "Attribute name is duplicated",
    "entity.form.validation.choiceLabelRequired":
      "Choice display name is required",
    "entity.form.validation.choicesRequired":
      "At least one choice is required when the select type is selected",
    "entity.form.validation.choiceLabelUnique":
      "Choice display names must be unique",
    "entity.form.choicesLabel": "Choices",
    "entity.form.choiceDisplayNamePlaceholder": "Choice display name",
    "entity.form.choiceInUseTooltip":
      "This choice cannot be deleted because it is used by an existing entry",
    "entity.form.addChoiceButton": "Add a choice",
    "entity.form.defaultObjectValuePlaceholder": "Default entry",

    // Entity history
    "entity.history.contentHeader": "Content",
    "entity.history.beforeHeader": "Before",
    "entity.history.afterHeader": "After",
    "entity.history.executedAtHeader": "Executed at",
    "entity.history.executedByHeader": "Executed by",
    "entity.history.opCreate": "Create",
    "entity.history.opModify": "Modify",
    "entity.history.opAddAttr": "Add attribute",
    "entity.history.opModAttr": "Modify attribute",
    "entity.history.opDelAttr": "Delete attribute",

    // Entity import modal
    "entity.import.title": "Import entities",
    "entity.import.description": "Please select a file to import.",
    "entity.import.caption": "* CSV files cannot be selected.",

    // Entity edit page
    "entity.edit.leaveConfirm":
      "Your changes will be lost if you leave this page. Are you sure you want to continue?",
    "entity.edit.errorDetail": 'Details: "{{message}}"',
    "entity.edit.loading": "Loading...",
    "entity.edit.newTitlePrefix": "New",
    "entity.edit.newEntityTitle": "Create a new entity",
    "entity.edit.description": "Entity details / edit",
  },
});
