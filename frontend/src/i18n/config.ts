import i18n, { Resource } from "i18next";
import { initReactI18next } from "react-i18next";

const resources: Resource = {
  en: {
    translation: {
      entities: "Entities",
      advancedSearch: "Advanced Search",
      management: "Management",
      manageUsers: "Manage users",
      manageGroups: "Manage groups",
      manageRoles: "Manage roles",
      previousVersion: "Previous version",
      currentUser: "is current user",
      userSetting: "User setting",
      logout: "Logout",
      noRunningJobs: "No running jobs",
      jobs: "Jobs",
    },
  },
  ja: {
    translation: {
      entities: "エンティティ一覧",
      advancedSearch: "高度な検索",
      management: "管理機能",
      manageUsers: "ユーザ管理",
      manageGroups: "グループ管理",
      manageRoles: "ロール管理",
      previousVersion: "旧デザイン",
      currentUser: "としてログイン",
      userSetting: "ユーザ設定",
      logout: "ログアウト",
      noRunningJobs: "実行タスクなし",
      jobs: "ジョブ一覧",
    },
  },
};

i18n.use(initReactI18next).init({
  resources,
  lng: "ja",
  interpolation: {
    escapeValue: false,
  },
});

export default i18n;
