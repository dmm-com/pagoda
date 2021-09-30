module.exports = {
  plugins: ['import'],
  rules: {},
  parserOptions: {
    sourceType: "module",
    ecmaVersion: 11,
    ecmaFeatures: {
      jsx: true,
    }
  },
  overrides: [
    {
      files: ['frontend/src/**/*.{js,jsx}'],
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
