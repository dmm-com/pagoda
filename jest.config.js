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
  setupFilesAfterEnv: [
    "@testing-library/jest-dom/extend-expect",
  ],
  moduleDirectories: [
    "frontend/src",
    "node_modules"
  ],
  transformIgnorePatterns: [],
}
