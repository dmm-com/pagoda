import path from "node:path";
import { fileURLToPath } from "node:url";

import tsconfigPaths from "vite-tsconfig-paths";
import { defineConfig } from "vitest/config";

import { checkFrontendCoverageThresholds } from "./tools/checkFrontendCoverageThresholds";
import { frontendSrcResolver } from "./tools/viteFrontendSrcResolver";

const rootDir = path.dirname(fileURLToPath(import.meta.url));
const frontendSrc = path.resolve(rootDir, "frontend/src");

export default defineConfig({
  plugins: [frontendSrcResolver(frontendSrc), tsconfigPaths()],
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./vitest.setup.ts"],
    include: ["frontend/src/**/*.{test,spec}.{ts,tsx}"],
    coverage: {
      provider: "v8",
      reportsDirectory: "./coverage",
      include: ["frontend/src/**/*.{ts,tsx}"],
      exclude: [
        "frontend/src/**/*.test.{ts,tsx}",
        "frontend/src/**/index.ts",
        "frontend/src/TestWrapper.tsx",
      ],
      reporter: ["text", "lcov"],
      thresholds: {
        statements: 75,
        branches: 55,
        functions: 60,
        lines: 75,
      },
    },
    onFinished: async () => {
      const coverageError = checkFrontendCoverageThresholds(rootDir);
      if (coverageError) {
        throw coverageError;
      }
    },
  },
});
