import { defineMessages } from "../defineMessages";

export const advancedSearchMessages = defineMessages({
  ja: {
    // AdvancedSearchModal
    "advancedSearch.modal.resetAttrTitle": "検索属性の再設定",
    "advancedSearch.modal.selectAttrPlaceholder": "属性を選択",
    "advancedSearch.modal.includeReferral": "参照アイテムも含める",

    // AdvancedSearchEditModal
    "advancedSearch.editModal.bulkUpdateTitle":
      "一括更新する（変更後の）値に更新",
    "advancedSearch.editModal.bulkUpdateSucceeded":
      "属性「{{attrName}}」の一括更新のジョブを実行しました（順次結果が反映されます）。",

    // AdvancedSearchJoinModal
    "advancedSearch.joinModal.title": "結合するアイテムの属性名",

    // SearchResultsTableHead
    "advancedSearch.tableHead.entryName": "アイテム名",
    "advancedSearch.tableHead.filterByEntryName": "アイテム名でフィルタ",
    "advancedSearch.tableHead.joinAttr": "アイテムの属性を結合する",
    "advancedSearch.tableHead.filterByAttrValue": "属性値でフィルタ",
    "advancedSearch.tableHead.referral": "参照アイテム",
    "advancedSearch.tableHead.filterByReferral": "参照アイテムでフィルタ",

    // SearchResultControlMenu (shared with ForEntry/ForReferral)
    "advancedSearch.controlMenu.filterConditions": "絞り込み条件",
    "advancedSearch.controlMenu.clear": "クリア",
    "advancedSearch.controlMenu.empty": "空白",
    "advancedSearch.controlMenu.nonEmpty": "空白ではない",
    "advancedSearch.controlMenu.duplicated": "重複",
    "advancedSearch.controlMenu.rangeSpecifyDate": "範囲で指定する",
    "advancedSearch.controlMenu.containsDate": "次を含む日付",
    "advancedSearch.controlMenu.notContainsDate": "次を含まない日付",
    "advancedSearch.controlMenu.rangeSpecify": "範囲指定",
    "advancedSearch.controlMenu.containsDateTime": "次を含む日時",
    "advancedSearch.controlMenu.notContainsDateTime": "次を含まない日時",
    "advancedSearch.controlMenu.trueOnly": "true のみ",
    "advancedSearch.controlMenu.falseOnly": "false のみ",
    "advancedSearch.controlMenu.containsText": "次を含むテキスト",
    "advancedSearch.controlMenu.notContainsText": "次を含まないテキスト",
    "advancedSearch.controlMenu.otherFunctions": "その他機能",
    "advancedSearch.controlMenu.bulkUpdate": "一括更新",
    "advancedSearch.controlMenu.showStats": "集計表示",
    "advancedSearch.controlMenu.includeModel": "次のモデルを含む",
    "advancedSearch.controlMenu.excludeModel": "次のモデルを含まない",

    // AdvancedSearchPage
    "advancedSearch.page.breadcrumb": "高度な検索",
    "advancedSearch.page.title": "高度な検索",
    "advancedSearch.page.search": "検索",
    "advancedSearch.page.targetModel": "検索対象のモデル",
    "advancedSearch.page.selectModelPlaceholder": "モデルを選択",
    "advancedSearch.page.searchAllEntities": "検索対象を絞り込まない",
    "advancedSearch.page.attr": "属性",
    "advancedSearch.page.selectAll": "すべて選択",
    "advancedSearch.page.selectAttrPlaceholder": "属性を選択",
    "advancedSearch.page.includeReferral": "参照アイテムも含める",

    // AdvancedSearchResultsPage
    "advancedSearch.resultsPage.breadcrumb": "高度な検索",
    "advancedSearch.resultsPage.title": "検索結果",
    "advancedSearch.resultsPage.filterLabelEmpty": "(空白)",
    "advancedSearch.resultsPage.filterLabelNonEmpty": "(空白ではない)",
    "advancedSearch.resultsPage.filterLabelDuplicated": "(重複している)",
    "advancedSearch.resultsPage.filterLabelContains": "「{{keyword}}」を含む",
    "advancedSearch.resultsPage.filterLabelNotContains":
      "「{{keyword}}」を含まない",
    "advancedSearch.resultsPage.deleteAllMatchedItems":
      "以下の条件にマッチする未選択の全てのアイテムを削除する",
    "advancedSearch.resultsPage.deleteAllMatchedItemsCaption":
      "（↑のチェックを入れない場合、一覧で選択したアイテムのみ削除されます）",
    "advancedSearch.resultsPage.attrValueIs": "属性「{{attrName}}」の値が",
    "advancedSearch.resultsPage.deleteAllUnselectedItems":
      "未選択の全てのアイテムもまとめて削除する",
    "advancedSearch.resultsPage.bulkDeleteSucceeded":
      "複数アイテムの削除に成功しました",
    "advancedSearch.resultsPage.bulkDeleteFailed":
      "複数アイテムの削除に失敗しました",
    "advancedSearch.resultsPage.searchInProgress": "検索中...",
    "advancedSearch.resultsPage.searchCountProgress":
      "{{count}} / {{totalCount}} 件",
    "advancedSearch.resultsPage.searchCount": "{{count}} 件",
    "advancedSearch.resultsPage.resetAttr": "属性の再設定",
    "advancedSearch.resultsPage.exportYaml": "YAML 出力",
    "advancedSearch.resultsPage.exportCsv": "CSV 出力",
    "advancedSearch.resultsPage.bulkDelete": "まとめて削除",
    "advancedSearch.resultsPage.confirmDeleteTitle": "本当に削除しますか？",
  },
  en: {
    // AdvancedSearchModal
    "advancedSearch.modal.resetAttrTitle": "Reset search attributes",
    "advancedSearch.modal.selectAttrPlaceholder": "Select attributes",
    "advancedSearch.modal.includeReferral": "Include referral entries",

    // AdvancedSearchEditModal
    "advancedSearch.editModal.bulkUpdateTitle":
      "Update to the (changed) value for bulk update",
    "advancedSearch.editModal.bulkUpdateSucceeded":
      'Started the bulk update job for attribute "{{attrName}}" (results will be reflected sequentially).',

    // AdvancedSearchJoinModal
    "advancedSearch.joinModal.title": "Attribute name of the item to join",

    // SearchResultsTableHead
    "advancedSearch.tableHead.entryName": "Item name",
    "advancedSearch.tableHead.filterByEntryName": "Filter by item name",
    "advancedSearch.tableHead.joinAttr": "Join item attribute",
    "advancedSearch.tableHead.filterByAttrValue": "Filter by attribute value",
    "advancedSearch.tableHead.referral": "Referral item",
    "advancedSearch.tableHead.filterByReferral": "Filter by referral item",

    // SearchResultControlMenu (shared with ForEntry/ForReferral)
    "advancedSearch.controlMenu.filterConditions": "Filter conditions",
    "advancedSearch.controlMenu.clear": "Clear",
    "advancedSearch.controlMenu.empty": "Empty",
    "advancedSearch.controlMenu.nonEmpty": "Not empty",
    "advancedSearch.controlMenu.duplicated": "Duplicated",
    "advancedSearch.controlMenu.rangeSpecifyDate": "Specify a range",
    "advancedSearch.controlMenu.containsDate": "Contains the following date",
    "advancedSearch.controlMenu.notContainsDate":
      "Does not contain the following date",
    "advancedSearch.controlMenu.rangeSpecify": "Range specification",
    "advancedSearch.controlMenu.containsDateTime":
      "Contains the following date/time",
    "advancedSearch.controlMenu.notContainsDateTime":
      "Does not contain the following date/time",
    "advancedSearch.controlMenu.trueOnly": "True only",
    "advancedSearch.controlMenu.falseOnly": "False only",
    "advancedSearch.controlMenu.containsText": "Contains the following text",
    "advancedSearch.controlMenu.notContainsText":
      "Does not contain the following text",
    "advancedSearch.controlMenu.otherFunctions": "Other functions",
    "advancedSearch.controlMenu.bulkUpdate": "Bulk update",
    "advancedSearch.controlMenu.showStats": "Show statistics",
    "advancedSearch.controlMenu.includeModel": "Include the following model",
    "advancedSearch.controlMenu.excludeModel": "Exclude the following model",

    // AdvancedSearchPage
    "advancedSearch.page.breadcrumb": "Advanced Search",
    "advancedSearch.page.title": "Advanced Search",
    "advancedSearch.page.search": "Search",
    "advancedSearch.page.targetModel": "Target models to search",
    "advancedSearch.page.selectModelPlaceholder": "Select models",
    "advancedSearch.page.searchAllEntities":
      "Do not narrow down search targets",
    "advancedSearch.page.attr": "Attributes",
    "advancedSearch.page.selectAll": "Select all",
    "advancedSearch.page.selectAttrPlaceholder": "Select attributes",
    "advancedSearch.page.includeReferral": "Include referral entries",

    // AdvancedSearchResultsPage
    "advancedSearch.resultsPage.breadcrumb": "Advanced Search",
    "advancedSearch.resultsPage.title": "Search results",
    "advancedSearch.resultsPage.filterLabelEmpty": "(Empty)",
    "advancedSearch.resultsPage.filterLabelNonEmpty": "(Not empty)",
    "advancedSearch.resultsPage.filterLabelDuplicated": "(Duplicated)",
    "advancedSearch.resultsPage.filterLabelContains": 'Contains "{{keyword}}"',
    "advancedSearch.resultsPage.filterLabelNotContains":
      'Does not contain "{{keyword}}"',
    "advancedSearch.resultsPage.deleteAllMatchedItems":
      "Delete all unselected items matching the following conditions",
    "advancedSearch.resultsPage.deleteAllMatchedItemsCaption":
      "(If you do not check the box above, only the items selected in the list will be deleted)",
    "advancedSearch.resultsPage.attrValueIs":
      'The value of attribute "{{attrName}}" is',
    "advancedSearch.resultsPage.deleteAllUnselectedItems":
      "Also delete all unselected items in bulk",
    "advancedSearch.resultsPage.bulkDeleteSucceeded":
      "Successfully deleted multiple items",
    "advancedSearch.resultsPage.bulkDeleteFailed":
      "Failed to delete multiple items",
    "advancedSearch.resultsPage.searchInProgress": "Searching...",
    "advancedSearch.resultsPage.searchCountProgress":
      "Results: {{count}} / {{totalCount}}",
    "advancedSearch.resultsPage.searchCount": "Results: {{count}}",
    "advancedSearch.resultsPage.resetAttr": "Reset attributes",
    "advancedSearch.resultsPage.exportYaml": "Export YAML",
    "advancedSearch.resultsPage.exportCsv": "Export CSV",
    "advancedSearch.resultsPage.bulkDelete": "Bulk delete",
    "advancedSearch.resultsPage.confirmDeleteTitle":
      "Are you sure you want to delete?",
  },
});
