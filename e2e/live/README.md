# Live e2e suite

The suite in `e2e/` runs the frontend bundle against `e2e/server.mjs`, a mock
API. That is enough to check the UI, but not features whose behaviour lives in
the backend -- permissions, validation, transactions. This suite fills that gap
by driving a real Django server and a real database.

It is not part of `npm run test:e2e` and is not run in CI: it needs MySQL,
Elasticsearch and a populated database, so it is a tool for verifying a change
locally, on demand.

## Running it

```sh
docker compose up -d mysql elasticsearch rabbitmq

export AIRONE_MYSQL_MASTER_URL="mysql://airone:password@127.0.0.1:3306/airone_e2e?charset=utf8mb4"
uv run python manage.py migrate
uv run python tools/generate_testdata.py 60 30   # any reasonable amount of data

# an admin account the suite can log in with (E2E_USERNAME / E2E_PASSWORD)
uv run python manage.py createsuperuser --username admin

npm run build
uv run python manage.py runserver 8000 &

npx playwright test --config=e2e/live/playwright.config.ts
```

The report and its screenshots are written to `e2e/test-results/report/`.
