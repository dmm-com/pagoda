// Vitest setup: initialize the real i18n instance and pin the language to
// Japanese so existing assertions on Japanese text keep working.
// Tests that exercise English can call `i18n.changeLanguage("en")`;
// the language is reset after each test.
import i18n from "./frontend/src/i18n/config";

// Called at module top-level (not in beforeAll) so that messages evaluated at
// import time of the test file (e.g. zod schemas) are already in Japanese.
// With inline resources, changeLanguage applies synchronously.
void i18n.changeLanguage("ja");

afterEach(async () => {
  if (i18n.language !== "ja") {
    await i18n.changeLanguage("ja");
  }
});
