#!/bin/bash

set -e

#
# NOTE it expects your gcloud config is set to the correct project and instance
#

INSTANCE="pagoda"
DATABASE="pagoda"

echo "Checking if database exists..."
if gcloud spanner databases list --instance=$INSTANCE --format="value(name)" | grep -q "$DATABASE"; then
    echo "Database exists. Dropping..."
    gcloud spanner databases delete $DATABASE \
        --instance=$INSTANCE \
        --quiet
fi

echo "Creating new database..."
gcloud spanner databases create $DATABASE \
    --instance=$INSTANCE \
    --ddl-file="entry/spanner/schema.sql"

echo "Inserting seed data..."
gcloud spanner databases execute-sql $DATABASE \
    --instance=$INSTANCE \
    --sql="$(cat entry/spanner/seed1.sql)"
gcloud spanner databases execute-sql $DATABASE \
    --instance=$INSTANCE \
    --sql="$(cat entry/spanner/seed2.sql)"
gcloud spanner databases execute-sql $DATABASE \
    --instance=$INSTANCE \
    --sql="$(cat entry/spanner/seed3.sql)"

echo "Database initialization completed successfully."
