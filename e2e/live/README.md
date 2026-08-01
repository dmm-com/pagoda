# Live e2e suite

The suite in `e2e/` runs the frontend bundle against `e2e/server.mjs`, a mock
API. That is enough to check the UI, but not features whose behaviour lives in
the backend -- permissions, validation, background jobs. This suite fills that
gap by driving a real Django server, a real database and a real Celery worker.

It is not part of `npm run test:e2e` and is not run in CI: it needs MySQL,
Elasticsearch, RabbitMQ and a populated database, so it is a tool for verifying
a change locally, on demand.

## Running it

```sh
docker compose up -d mysql elasticsearch rabbitmq

# A dedicated database and message vhost, so that a worker started here cannot
# pick up jobs queued by another checkout and run them against the wrong data.
docker exec rabbitmq rabbitmqctl add_vhost e2e
docker exec rabbitmq rabbitmqctl set_permissions -p e2e guest ".*" ".*" ".*"
export AIRONE_MYSQL_MASTER_URL="mysql://airone:password@127.0.0.1:3306/airone_e2e?charset=utf8mb4"
export AIRONE_RABBITMQ_URL="amqp://guest:guest@localhost/e2e"

uv run python manage.py migrate
uv run python tools/generate_testdata.py 60 30   # any reasonable amount of data

# an admin account the suite can log in with (E2E_USERNAME / E2E_PASSWORD)
uv run python manage.py createsuperuser --username admin

npm run build
uv run python manage.py runserver 8000 &
uv run celery --app airone worker -l info &

npx playwright test --config=e2e/live/playwright.config.ts
```

Import previews run as Celery jobs, so the worker is not optional -- without it
the dialog polls a job that never starts. The worker does **not** reload code:
restart it after changing anything under `*/tasks.py`, or it will keep running
the version it was started with.

The report and its screenshots are written to `e2e/test-results/report/`.
