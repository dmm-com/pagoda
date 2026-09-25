/**
 */

import { act, renderHook } from "@testing-library/react";
import i18next from "i18next";
import { FC, ReactNode } from "react";
import { I18nextProvider } from "react-i18next";

import appI18n from "../i18n/config";

import { useTranslation } from "./useTranslation";

// Use a dedicated instance (not the shared i18next default singleton) so this
// mock configuration does not clobber the real app i18n instance used below.
const i18n = i18next.createInstance();

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

describe("useTranslation with the real app i18n instance", () => {
  const appWrapper: FC<{ children: ReactNode }> = ({ children }) => (
    <I18nextProvider i18n={appI18n}>{children}</I18nextProvider>
  );

  afterEach(async () => {
    await act(async () => {
      await appI18n.changeLanguage("ja");
    });
  });

  test("returns Japanese text for a real key by default", () => {
    const { result } = renderHook(() => useTranslation(), {
      wrapper: appWrapper,
    });

    expect(result.current.t("common.cancel")).toBe("キャンセル");
  });

  test("returns English text for a real key after changing language", async () => {
    const { result } = renderHook(() => useTranslation(), {
      wrapper: appWrapper,
    });

    await act(async () => {
      await appI18n.changeLanguage("en");
    });

    expect(result.current.t("common.cancel")).toBe("Cancel");
  });

  test("interpolates values via options", async () => {
    const { result } = renderHook(() => useTranslation(), {
      wrapper: appWrapper,
    });

    expect(
      result.current.t("notification.jobCompleted", { label: "Test job" }),
    ).toBe("Test jobが完了しました");

    await act(async () => {
      await appI18n.changeLanguage("en");
    });

    expect(
      result.current.t("notification.jobCompleted", { label: "Test job" }),
    ).toBe("Test job completed");
  });

  test("t keeps a stable identity across re-renders", () => {
    const { result, rerender } = renderHook(() => useTranslation(), {
      wrapper: appWrapper,
    });
    const first = result.current.t;
    rerender();
    expect(result.current.t).toBe(first);
  });

  test("t is refreshed and translates in the new language after a language change", async () => {
    const { result } = renderHook(() => useTranslation(), {
      wrapper: appWrapper,
    });
    expect(result.current.t("common.cancel")).toBe("キャンセル");
    await act(async () => {
      await appI18n.changeLanguage("en");
    });
    expect(result.current.t("common.cancel")).toBe("Cancel");
  });
});
