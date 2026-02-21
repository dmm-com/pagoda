const path = require('path');

module.exports = {
  ignorePatterns: [
    'frontend/dist/',
    'frontend/plugins/*/dist/',
    '**/node_modules/',
    '**/*.min.js',
    'static/js/',
  ],
  plugins: ['import', 'unused-imports', 'react', 'react-hooks', 'react-you-might-not-need-an-effect', '@typescript-eslint'],
  settings: {
    'import/resolver': {
      webpack: {
        config: path.resolve('webpack.config.js')
      },
    },
    "react": {
      "version": "detect",
    },
  },
  rules: {
    'react/react-in-jsx-scope': 'off',
    'react/jsx-uses-react': 'off',
    'react/jsx-uses-vars': 'error',
    'unused-imports/no-unused-imports': 'error',
    "no-restricted-imports": [
      "error",
      {
        "paths": [{
          "name": "@mui/icons-material",
          "message": "import @mui/icons-material/ICONNAME instead.",
        }],
      },
    ],
    "no-unused-vars": "off",
    "@typescript-eslint/no-unused-vars": "error",
    "@typescript-eslint/no-explicit-any": "error",
    'react-hooks/rules-of-hooks': 'error',
    'react-hooks/exhaustive-deps': 'warn',
  },
  parser: '@typescript-eslint/parser',
  parserOptions: {
    sourceType: "module",
    ecmaVersion: 11,
    ecmaFeatures: {
      jsx: true,
    }
  },
  extends: [
    'plugin:@typescript-eslint/recommended',
    'plugin:react/recommended',
    'plugin:react-you-might-not-need-an-effect/legacy-recommended',
  ],
  overrides: [
    {
      files: ['frontend/src/**/*.{js,jsx,ts,tsx}'],
      rules: {
        'sort/imports': 0,
        'import/order': [
          'error',
          {
            groups: [
              'builtin',
              'external',
              'parent',
              'sibling',
              'index',
              'object',
              'type',
            ],
            alphabetize: {
              order: 'asc',
            },
            'newlines-between': 'always',
          },
        ],
      },
    },
  ],
};
