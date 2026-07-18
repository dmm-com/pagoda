module.exports = {
  roots: [
    "frontend/src"
  ],
  testMatch: [
    "**/__tests__/**/*.+(ts|tsx|js)",
    "**/?(*.)+(spec|test).+(ts|tsx|js)"
  ],
  transform: {
    "^.+\\.(ts|tsx)$": "ts-jest"
  },
  setupFiles: [
      "./jest.polyfills.js",
  ],
  setupFilesAfterEnv: [
    "@testing-library/jest-dom/extend-expect",
  ],
  collectCoverageFrom: [
    "frontend/src/**/*.{ts,tsx}",
    "!frontend/src/**/*.test.{ts,tsx}",
    "!frontend/src/**/index.ts",
    "!frontend/src/TestWrapper.tsx",
  ],
  coverageThreshold: {
    global: {
      statements: 75,
      branches: 55,
      functions: 60,
      lines: 75,
    },
  },
  reporters: ["default", "<rootDir>/tools/frontendCoverageReporter.cjs"],
  moduleDirectories: [
    "frontend/src",
    "node_modules"
  ],
  moduleNameMapper: {},
  transformIgnorePatterns: [],
  testEnvironment: "jsdom",
  testEnvironmentOptions: {
    // to integrate msw 2.x
    // ref. https://mswjs.io/docs/migrations/1.x-to-2.x/#cannot-find-module-mswnode-jsdom
    customExportConditions: [""],
  },
}
