import i18n, { detectLanguage, translate } from "./config";
import { en, ja } from "./locales";
import { aclMessages } from "./locales/acl";
import { advancedSearchMessages } from "./locales/advancedSearch";
import { categoryMessages } from "./locales/category";
import { commonMessages } from "./locales/common";
import { entityMessages } from "./locales/entity";
import { entryMessages } from "./locales/entry";
import { entryFormMessages } from "./locales/entryForm";
import { groupMessages } from "./locales/group";
import { headerMessages } from "./locales/header";
import { jobMessages } from "./locales/job";
import { roleMessages } from "./locales/role";
import { triggerMessages } from "./locales/trigger";
import { userMessages } from "./locales/user";

const domainMessages = {
  acl: aclMessages,
  advancedSearch: advancedSearchMessages,
  category: categoryMessages,
  common: commonMessages,
  entity: entityMessages,
  entry: entryMessages,
  entryForm: entryFormMessages,
  group: groupMessages,
  header: headerMessages,
  job: jobMessages,
  role: roleMessages,
  trigger: triggerMessages,
  user: userMessages,
};

describe("i18n resources", () => {
  test("every domain file is merged and no key is defined in two domains", () => {
    const owners = new Map<string, string[]>();
    for (const [domain, messages] of Object.entries(domainMessages)) {
      for (const key of Object.keys(messages.ja)) {
        owners.set(key, [...(owners.get(key) ?? []), domain]);
      }
    }
    const duplicated = [...owners.entries()].filter(
      ([, domains]) => domains.length > 1,
    );
    expect(duplicated).toEqual([]);
    expect(Object.keys(ja).sort()).toEqual([...owners.keys()].sort());
  });

  test("ja and en have identical key sets", () => {
    const jaKeys = Object.keys(ja).sort();
    const enKeys = Object.keys(en).sort();
    expect(jaKeys).toEqual(enKeys);
  });

  test("no empty values in either language", () => {
    for (const value of Object.values(ja)) {
      expect(value).not.toBe("");
    }
    for (const value of Object.values(en)) {
      expect(value).not.toBe("");
    }
  });

  test("en values contain no Japanese characters", () => {
    const japanese = /[぀-ヿ一-鿿]/;
    const offending = Object.entries(en).filter(([, value]) =>
      japanese.test(value),
    );
    expect(offending).toEqual([]);
  });

  test("placeholder names match between ja and en for every key", () => {
    const extractPlaceholders = (value: string): string[] =>
      [...value.matchAll(/{{\s*([\w.]+)\s*}}/g)].map((m) => m[1]).sort();

    for (const key of Object.keys(ja)) {
      const jaPlaceholders = extractPlaceholders(
        (ja as Record<string, string>)[key],
      );
      const enPlaceholders = extractPlaceholders(
        (en as Record<string, string>)[key],
      );
      expect({ key, placeholders: enPlaceholders }).toEqual({
        key,
        placeholders: jaPlaceholders,
      });
    }
  });
});

describe("detectLanguage", () => {
  test("picks ja/en from a mixed language list preferring the first match", () => {
    expect(detectLanguage(["en-US", "ja"])).toBe("en");
  });

  test("picks ja from a ja-JP locale", () => {
    expect(detectLanguage(["ja-JP"])).toBe("ja");
  });

  test("returns undefined when no supported language matches", () => {
    expect(detectLanguage(["fr-FR"])).toBeUndefined();
  });

  test("returns undefined when languages is undefined", () => {
    expect(detectLanguage(undefined)).toBeUndefined();
  });
});

describe("translate", () => {
  afterEach(async () => {
    await i18n.changeLanguage("ja");
  });

  test("returns ja by default in tests", () => {
    expect(translate("common.cancel")).toBe("キャンセル");
  });

  test("returns English after changing language to en", async () => {
    await i18n.changeLanguage("en");
    expect(translate("common.cancel")).toBe("Cancel");
  });

  test("interpolates placeholders", () => {
    expect(translate("notification.jobCompleted", { label: "Test job" })).toBe(
      "Test jobが完了しました",
    );
  });

  test("interpolates placeholders in English", async () => {
    await i18n.changeLanguage("en");
    expect(translate("notification.jobCompleted", { label: "Test job" })).toBe(
      "Test job completed",
    );
  });
});
