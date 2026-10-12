import { defineMessages } from "../defineMessages";

export const categoryMessages = defineMessages({
  ja: {
    // CategoryList / CategoryListPage / ListCategoryPage
    "category.list.title": "カテゴリ一覧",
    "category.list.searchPlaceholder": "カテゴリを絞り込む",
    "category.list.createButton": "新規カテゴリを作成",

    // CategoryControlMenu
    "category.menu.acl": "ACL 設定",
    "category.menu.confirmDelete": "本当に削除しますか？",
    "category.menu.deleteSuccess": "カテゴリの削除が完了しました",
    "category.menu.deleteFailed": "カテゴリの削除が失敗しました",

    // CategoryForm / CategoryFormSchema
    "category.form.item": "項目",
    "category.form.content": "内容",
    "category.form.name": "カテゴリ名",
    "category.form.note": "備考",
    "category.form.models": "登録モデル(複数可)",
    "category.form.modelsPlaceholder": "モデルを選択",
    "category.form.priority": "表示優先度",
    "category.form.nameRequired": "カテゴリ名は必須です",
    "category.form.confirmLeave":
      "編集した内容は失われてしまいますが、このページを離れてもよろしいですか？",

    // CategoryEditPage
    "category.edit.breadcrumb": "カテゴリ編集",
    "category.edit.createTitle": "新規カテゴリの作成",
    "category.edit.errorDetail": '詳細: "{{message}}"',
  },
  en: {
    // CategoryList / CategoryListPage / ListCategoryPage
    "category.list.title": "Category list",
    "category.list.searchPlaceholder": "Filter categories",
    "category.list.createButton": "Create new category",

    // CategoryControlMenu
    "category.menu.acl": "ACL settings",
    "category.menu.confirmDelete": "Are you sure you want to delete this?",
    "category.menu.deleteSuccess": "Successfully deleted the category",
    "category.menu.deleteFailed": "Failed to delete the category",

    // CategoryForm / CategoryFormSchema
    "category.form.item": "Item",
    "category.form.content": "Content",
    "category.form.name": "Category name",
    "category.form.note": "Note",
    "category.form.models": "Registered models (multiple allowed)",
    "category.form.modelsPlaceholder": "Select models",
    "category.form.priority": "Display priority",
    "category.form.nameRequired": "Category name is required",
    "category.form.confirmLeave":
      "Any changes you made will be lost. Are you sure you want to leave this page?",

    // CategoryEditPage
    "category.edit.breadcrumb": "Edit category",
    "category.edit.createTitle": "Create a new category",
    "category.edit.errorDetail": 'Details: "{{message}}"',
  },
});
