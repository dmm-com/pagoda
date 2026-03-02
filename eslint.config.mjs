import tseslint from "typescript-eslint";
import reactPlugin from "eslint-plugin-react";
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
