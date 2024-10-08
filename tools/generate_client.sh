#!/bin/bash

set -u

OPENAPI_GENERATOR_VERSION=v7.8.0
dst=${1:-frontend/src/apiclient/autogenerated}

# Check if "--docker" is passed as an argument
if [[ $@ == *"--docker"* ]]; then
  CHECK_CMD="docker compose exec -e DJANGO_CONFIGURATION=${DJANGO_CONFIGURATION:-} -w /workspace/airone airone bash -lc 'poetry run python manage.py spectacular 2>&1 > /dev/null | grep ERROR'"
  SPECTACULAR_CMD="docker compose exec -e DJANGO_CONFIGURATION=${DJANGO_CONFIGURATION:-} -w /workspace/airone airone bash -lc 'poetry run python manage.py spectacular --file spec.yaml'"
  PRETTIER_CMD="docker compose exec -w /workspace/airone airone bash -lc 'npx prettier --write $dst'"
else
  CHECK_CMD="poetry run python manage.py spectacular 2>&1 > /dev/null | grep ERROR"
  SPECTACULAR_CMD="poetry run python manage.py spectacular --file spec.yaml"
  PRETTIER_CMD="npx prettier --write $dst"
fi


# detect errors on spectacular
generr=$(eval $CHECK_CMD)
if [ "$generr" != "" ]; then
  echo "Error(s) occur on generating OpenAPI spec from API implementation:";
  echo "$generr";
  exit 1;
fi

# generate OpenAPI spec
eval $SPECTACULAR_CMD;

# generate client code
docker run --rm -u "$(id -u):$(id -g)" -v "${PWD}:/local" openapitools/openapi-generator-cli:$OPENAPI_GENERATOR_VERSION generate -i /local/spec.yaml -g typescript-fetch -o /local/"$dst" --additional-properties=typescriptThreePlus=true;

# format client code
eval $PRETTIER_CMD;
