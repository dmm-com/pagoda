const path = require('path');

module.exports = {
  plugins: ['import', 'unused-imports', 'react', '@typescript-eslint'],
  settings: {
    'import/resolver': {
      webpack: {
        config: path.resolve('webpack.config.js')
      },
    },
  },
  rules: {
    'react/jsx-uses-react': 'error',
    'react/jsx-uses-vars': 'error',
    'unused-imports/no-unused-imports': 'error',
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
