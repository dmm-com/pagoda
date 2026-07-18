import path from "node:path";

import { defineConfig, devices } from "@playwright/test";

const port = Number(process.env.E2E_PORT ?? 4173);
const testResultsDir = path.resolve(process.cwd(), "e2e", "test-results");

export default defineConfig({
  testDir: ".",
  testMatch: /.*\.spec\.ts/,
  timeout: 30_000,
  expect: {
    timeout: 10_000,
  },
  fullyParallel: false,
  workers: 1,
  reporter: [
    ["list"],
    ["json", { outputFile: path.join(testResultsDir, "results.json") }],
    [
      "html",
      { open: "never", outputFolder: path.join(testResultsDir, "html") },
    ],
  ],
  outputDir: path.join(testResultsDir, "artifacts"),
  use: {
    baseURL: `http://127.0.0.1:${port}`,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  webServer: {
    command: `E2E_PORT=${port} node server.mjs`,
    url: `http://127.0.0.1:${port}/ui/`,
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
