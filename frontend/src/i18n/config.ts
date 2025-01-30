import i18n, { Resource } from "i18next";
import { initReactI18next } from "react-i18next";

export type TranslationKey =
  | "categories"
  | "entities"
  | "advancedSearch"
  | "management"
  | "manageUsers"
  | "manageGroups"
  | "manageRoles"
  | "manageTriggers"
  | "previousVersion"
  | "currentUser"
  | "userSetting"
  | "logout"
  | "noRunningJobs"
  | "jobs";

interface AironeResource {
  en: {
    translation: Record<TranslationKey, string>;
  };
  ja: {
    translation: Record<TranslationKey, string>;
  };
}

function toResource(resource: AironeResource): Resource {
  return {
    en: {
      translation: {
        ...resource.en.translation,
      },
    },
    ja: {
      translation: {
        ...resource.ja.translation,
      },
    },
  };
}

const resources = toResource({
  en: {
    translation: {
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
    },
  },
  ja: {
    translation: {
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
    },
  },
});

const primaryLanguage = window.navigator.languages
  .map((l) => l.slice(0, 2))
  .filter((l) => l === "ja" || l === "en")[0];

i18n.use(initReactI18next).init({
  resources,
  lng: primaryLanguage,
  fallbackLng: "ja",
  interpolation: {
    escapeValue: false,
  },
});

export default i18n;
