/**
 * @jest-environment jsdom
 */

import { renderHook } from "@testing-library/react";
import i18n from "i18next";
import { FC, ReactNode } from "react";
import { I18nextProvider } from "react-i18next";

import { useTranslation } from "./useTranslation";

// Initialize i18n for testing
i18n.init({
  lng: "ja",
  fallbackLng: "ja",
  resources: {
    ja: {
      translation: {
        testKey: "テスト値",
        hello: "こんにちは",
        entities: "エンティティ",
      },
    },
    en: {
      translation: {
        testKey: "Test Value",
        hello: "Hello",
        entities: "Entities",
      },
    },
  },
  interpolation: {
    escapeValue: false,
  },
});

const wrapper: FC<{ children: ReactNode }> = ({ children }) => (
  <I18nextProvider i18n={i18n}>{children}</I18nextProvider>
);

describe("useTranslation", () => {
  describe("return value structure", () => {
    test("should return t function", () => {
      const { result } = renderHook(() => useTranslation(), { wrapper });

      expect(result.current.t).toBeDefined();
      expect(typeof result.current.t).toBe("function");
    });

    test("should return i18n instance", () => {
      const { result } = renderHook(() => useTranslation(), { wrapper });

      expect(result.current.i18n).toBeDefined();
    });

    test("should return ready status", () => {
      const { result } = renderHook(() => useTranslation(), { wrapper });

      expect(result.current.ready).toBe(true);
    });

    test("should be array-like with destructuring support", () => {
      const { result } = renderHook(() => useTranslation(), { wrapper });

      const [t, i18nInstance, ready] = result.current;

      expect(typeof t).toBe("function");
      expect(i18nInstance).toBeDefined();
      expect(ready).toBe(true);
    });
  });

  describe("translation function", () => {
    test("should translate known keys", () => {
      const { result } = renderHook(() => useTranslation(), { wrapper });

      // Using 'entities' as it's a known translation key in the actual app
      const translated = result.current.t("entities" as never);

      expect(translated).toBeDefined();
      expect(typeof translated).toBe("string");
    });

    test("should return string type", () => {
      const { result } = renderHook(() => useTranslation(), { wrapper });

      const translated = result.current.t("entities" as never);

      expect(typeof translated).toBe("string");
    });
  });

  describe("i18n instance", () => {
    test("should have language property", () => {
      const { result } = renderHook(() => useTranslation(), { wrapper });

      expect(result.current.i18n.language).toBeDefined();
    });

    test("should have changeLanguage function", () => {
      const { result } = renderHook(() => useTranslation(), { wrapper });

      expect(typeof result.current.i18n.changeLanguage).toBe("function");
    });
  });

  describe("with options", () => {
    test("should accept namespace option", () => {
      const { result } = renderHook(
        () => useTranslation(undefined, undefined),
        { wrapper },
      );

      expect(result.current.t).toBeDefined();
    });
  });
});
