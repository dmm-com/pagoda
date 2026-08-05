import path from "node:path";

import { defineConfig, devices } from "@playwright/test";

/**
 * Configuration for the live suite: it drives a real Django server backed by a
 * real database, unlike the sibling suite in e2e/, which runs against the mock
 * server in e2e/server.mjs. Start the server yourself (see README.md) and point
 * E2E_BASE_URL at it.
 */
const testResultsDir = path.resolve(
  process.cwd(),
  "e2e",
  "live",
  "test-results",
);

export default defineConfig({
  testDir: ".",
  testMatch: /.*\.live-spec\.ts/,
  timeout: 120_000,
  expect: {
    timeout: 15_000,
  },
  fullyParallel: false,
  workers: 1,
  reporter: [
    ["list"],
    ["json", { outputFile: path.join(testResultsDir, "results.json") }],
  ],
  outputDir: path.join(testResultsDir, "artifacts"),
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://127.0.0.1:8000",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
