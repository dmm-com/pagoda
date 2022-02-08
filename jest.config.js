module.exports = {
  "roots": [
    "frontend/src"
  ],
  "testMatch": [
    "**/__tests__/**/*.+(ts|tsx|js)",
    "**/?(*.)+(spec|test).+(ts|tsx|js)"
  ],
  "transform": {
    "^.+\\.(ts|tsx)$": "ts-jest"
  },
  "setupFilesAfterEnv": [
    "<rootDir>/frontend/src/setupTests.ts"
  ],
  "moduleDirectories": [
    "frontend/src",
    "node_modules"
  ]
}
