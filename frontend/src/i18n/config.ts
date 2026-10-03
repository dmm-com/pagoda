import i18n from "i18next";
import { initReactI18next } from "react-i18next";

import { en, ja, TranslationKey } from "./locales";

export type { TranslationKey };

export const supportedLanguages = ["ja", "en"] as const;
export type SupportedLanguage = (typeof supportedLanguages)[number];

export type TranslationOptions = Record<string, string | number>;

export const resources = {
  ja: { translation: ja },
  en: { translation: en },
};

export function detectLanguage(
  languages: readonly string[] | undefined,
): SupportedLanguage | undefined {
  return (languages ?? [])
    .map((l) => l.slice(0, 2))
    .find((l): l is SupportedLanguage =>
      (supportedLanguages as readonly string[]).includes(l),
    );
}

const primaryLanguage = detectLanguage(
  typeof window !== "undefined" ? window.navigator.languages : undefined,
);

i18n.use(initReactI18next).init({
  resources,
  lng: primaryLanguage,
  fallbackLng: "ja",
  // Keys are flat strings such as "entry.form.name"; dots are not nesting.
  keySeparator: false,
  interpolation: {
    escapeValue: false,
  },
});

/**
 * Translates a key outside of React components (services, schemas, etc).
 * Inside components, prefer the useTranslation hook so the view re-renders
 * on language change.
 */
export function translate(
  key: TranslationKey,
  options?: TranslationOptions,
): string {
  return i18n.t(key, options);
}

export default i18n;
