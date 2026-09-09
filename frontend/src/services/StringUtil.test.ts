import { fuzzyMatch, normalizeToMatch } from "./StringUtil";

test("text should includes substring keyword with fuzzy conversions", () => {
  expect(normalizeToMatch("test")).toBe("test");
  expect(normalizeToMatch("TEST")).toBe("test");
  expect(normalizeToMatch("ｔｅｓｔ")).toBe("test");
  expect(normalizeToMatch("ﾊﾝｶｸ-ＢＩＧ-LARGE")).toBe("ハンカク-big-large");
});

test("text should includes substring keyword with fuzzy conversions", () => {
  expect(fuzzyMatch("test", "test")).toBe(true);
  expect(fuzzyMatch("this is a test case", "test")).toBe(true);

  // with conversions
  expect(fuzzyMatch("TEST", "test")).toBe(true);
  expect(fuzzyMatch("test", "TEST")).toBe(true);
  expect(fuzzyMatch("ｔｅｓｔ", "test")).toBe(true);
  expect(fuzzyMatch("test", "ｔｅｓｔ")).toBe(true);

  // Half-width Katakana, full-width uppercase, and half-width uppercase.
  expect(fuzzyMatch("ﾊﾝｶｸ-ＢＩＧ-LARGE", "ハンカク-big")).toBe(true);
  expect(fuzzyMatch("ﾊﾝｶｸ-ＢＩＧ-LARGE", "ﾊﾝｶｸ")).toBe(true);
  expect(fuzzyMatch("unrelated text", "test")).toBe(false);
});
