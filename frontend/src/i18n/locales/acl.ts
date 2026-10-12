import { defineMessages } from "../defineMessages";

export const aclMessages = defineMessages({
  ja: {
    // ACLForm
    "acl.form.item": "項目",
    "acl.form.content": "内容",
    "acl.form.isPublicLabel": "公開設定",
    "acl.form.public": "公開",
    "acl.form.limitedPublic": "限定公開",
    "acl.form.title": "公開制限設定",
    "acl.form.role": "ロール",
    "acl.form.note": "備考",
    "acl.form.everyone": "全員",
    "acl.form.limitedPublicRequiresFullRole":
      "限定公開にする場合は、いずれかのロールの権限を {{fullLabel}} にしてください",
    "acl.form.confirmLeave":
      "編集した内容は失われてしまいますが、このページを離れてもよろしいですか？",
    "acl.form.updateSuccess": "ACL設定の更新が成功しました",

    // ACL pages (shared between edit/history)
    "acl.page.title": "ACL設定",
    "acl.breadcrumb.categoryList": "カテゴリ一覧",

    // ACLHistoryList / ACLHistoryPage
    "acl.history.item": "項目",
    "acl.history.before": "変更前",
    "acl.history.after": "変更後",
    "acl.history.time": "実行日時",
    "acl.history.user": "実行者",
    "acl.history.isPublicLabel": "公開設定",
    "acl.history.public": "公開",
    "acl.history.limitedPublic": "限定公開",
    "acl.history.defaultPermission": "デフォルト権限",
    "acl.history.pageTitle": "ACL変更履歴",
  },
  en: {
    // ACLForm
    "acl.form.item": "Item",
    "acl.form.content": "Content",
    "acl.form.isPublicLabel": "Public setting",
    "acl.form.public": "Public",
    "acl.form.limitedPublic": "Limited public",
    "acl.form.title": "Public restriction settings",
    "acl.form.role": "Role",
    "acl.form.note": "Note",
    "acl.form.everyone": "Everyone",
    "acl.form.limitedPublicRequiresFullRole":
      "To set this to limited public, set at least one role's permission to {{fullLabel}}",
    "acl.form.confirmLeave":
      "Any changes you made will be lost. Are you sure you want to leave this page?",
    "acl.form.updateSuccess": "Successfully updated the ACL settings",

    // ACL pages (shared between edit/history)
    "acl.page.title": "ACL settings",
    "acl.breadcrumb.categoryList": "Category list",

    // ACLHistoryList / ACLHistoryPage
    "acl.history.item": "Item",
    "acl.history.before": "Before",
    "acl.history.after": "After",
    "acl.history.time": "Time",
    "acl.history.user": "User",
    "acl.history.isPublicLabel": "Public setting",
    "acl.history.public": "Public",
    "acl.history.limitedPublic": "Limited public",
    "acl.history.defaultPermission": "Default permission",
    "acl.history.pageTitle": "ACL history",
  },
});
