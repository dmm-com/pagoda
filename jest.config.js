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
  moduleDirectories: [
    "frontend/src",
    "node_modules"
  ],
  transformIgnorePatterns: [],
  testEnvironmentOptions: {
    // to integrate msw 2.x
    // ref. https://mswjs.io/docs/migrations/1.x-to-2.x/#cannot-find-module-mswnode-jsdom
    customExportConditions: [""],
  },
}
