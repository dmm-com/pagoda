import tseslint from "typescript-eslint";
import reactPlugin from "eslint-plugin-react";
import reactHooksPlugin from "eslint-plugin-react-hooks";
import reactYouMightNotNeedAnEffectPlugin from "eslint-plugin-react-you-might-not-need-an-effect";
import importXPlugin from "eslint-plugin-import-x";
import unusedImportsPlugin from "eslint-plugin-unused-imports";

export default tseslint.config(
  {
    ignores: [
      "frontend/dist/",
      "frontend/plugins/*/dist/",
      "**/node_modules/",
      "**/*.min.js",
      "static/js/",
    ],
  },
  ...tseslint.configs.recommended,
  reactPlugin.configs.flat.recommended,
  reactPlugin.configs.flat["jsx-runtime"],
  {
    plugins: {
      "import-x": importXPlugin,
      "unused-imports": unusedImportsPlugin,
      "react-hooks": reactHooksPlugin,
      "react-you-might-not-need-an-effect": reactYouMightNotNeedAnEffectPlugin,
    },
    settings: {
      "import-x/resolver": {
        typescript: { project: "./tsconfig.json" },
      },
      react: { version: "detect" },
    },
    rules: {
      "react/jsx-uses-vars": "error",
      "unused-imports/no-unused-imports": "error",
      "no-restricted-imports": [
        "error",
        {
          paths: [
            {
              name: "@mui/icons-material",
              message:
                "import @mui/icons-material/ICONNAME instead.",
            },
          ],
        },
      ],
      "no-unused-vars": "off",
      "@typescript-eslint/no-unused-vars": [
        "error",
        { caughtErrors: "none" },
      ],
      "@typescript-eslint/no-explicit-any": "error",
      "@typescript-eslint/no-unused-expressions": "off",
      "react-hooks/rules-of-hooks": "error",
      "react-hooks/exhaustive-deps": "warn",
      "react-you-might-not-need-an-effect/no-empty-effect": "warn",
      "react-you-might-not-need-an-effect/no-adjust-state-on-prop-change": "warn",
      "react-you-might-not-need-an-effect/no-reset-all-state-on-prop-change": "warn",
      "react-you-might-not-need-an-effect/no-event-handler": "warn",
      "react-you-might-not-need-an-effect/no-pass-live-state-to-parent": "warn",
      "react-you-might-not-need-an-effect/no-pass-data-to-parent": "warn",
      "react-you-might-not-need-an-effect/no-initialize-state": "warn",
      "react-you-might-not-need-an-effect/no-chain-state-updates": "warn",
      "react-you-might-not-need-an-effect/no-derived-state": "warn",
    },
  },
  {
    files: ["frontend/src/**/*.{js,jsx,ts,tsx}"],
    rules: {
      "import-x/order": [
        "error",
        {
          groups: [
            "builtin",
            "external",
            "parent",
            "sibling",
            "index",
            "object",
            "type",
          ],
          alphabetize: { order: "asc" },
          "newlines-between": "always",
        },
      ],
    },
  }
);
