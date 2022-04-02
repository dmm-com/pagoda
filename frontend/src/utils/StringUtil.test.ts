import { fuzzyMatch } from "./StringUtil";

test("text should includes substring keyword with fuzzy conversions", () => {
  expect(fuzzyMatch("test", "test")).toBe(true);
  expect(fuzzyMatch("this is a test case", "test")).toBe(true);

  // with conversions
  expect(fuzzyMatch("TEST", "test")).toBe(true);
  expect(fuzzyMatch("test", "TEST")).toBe(true);
  expect(fuzzyMatch("ｔｅｓｔ", "test")).toBe(true);
  expect(fuzzyMatch("test", "ｔｅｓｔ")).toBe(true);

  expect(fuzzyMatch("unrelated text", "test")).toBe(false);
});
