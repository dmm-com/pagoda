import { defineMessages } from "../defineMessages";

// These keys predate the domain-prefixed naming and are kept as-is because
// custom views may reference them.
export const headerMessages = defineMessages({
  ja: {
    categories: "カテゴリ一覧",
    entities: "モデル一覧",
    advancedSearch: "高度な検索",
    management: "管理機能",
    manageUsers: "ユーザ管理",
    manageGroups: "グループ管理",
    manageRoles: "ロール管理",
    manageTriggers: "トリガー管理",
    previousVersion: "旧デザイン",
    currentUser: "としてログイン",
    userSetting: "ユーザ設定",
    logout: "ログアウト",
    noRunningJobs: "実行タスクなし",
    jobs: "ジョブ一覧",
    "header.unknownUser": "不明なユーザ",
  },
  en: {
    categories: "Categories",
    entities: "Entities",
    advancedSearch: "Advanced Search",
    management: "Management",
    manageUsers: "Manage users",
    manageGroups: "Manage groups",
    manageRoles: "Manage roles",
    manageTriggers: "Manage triggers",
    previousVersion: "Previous version",
    currentUser: "is current user",
    userSetting: "User setting",
    logout: "Logout",
    noRunningJobs: "No running jobs",
    jobs: "Jobs",
    "header.unknownUser": "Unknown user",
  },
});
