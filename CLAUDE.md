# CLAUDE.md - Guide for Agentic Assistants working with Airone

## Build, Lint, and Test Commands
- Python: `poetry run python manage.py test [app_name.tests.test_file.TestClass.test_method]`
- Run specific frontend test: `npm run test -- -t "test name pattern"`
- Lint frontend: `npm run lint`
- Fix frontend linting issues: `npm run fix`
- Build frontend: `npm run build`
- Build production frontend: `npm run build:production`

## Code Style Guidelines
- Python: Follow PEP 8, max line length 100 chars (enforced by ruff)
- TypeScript: Use strict typing, follow ESLint rules
- Django: Follow Django project structure with apps organization
- React: Functional components with hooks preferred
- Error handling: Use try/except with specific exceptions in Python
- Frontend naming: PascalCase for components, camelCase for variables/functions
- Frontend imports: Group by external/internal, sort alphabetically
- Always add type annotations in TypeScript
- **Comments and documentation**: Write all comments and docstrings in English, never in Japanese or other languages

Follow repository conventions for similar code. Check existing files for guidance.