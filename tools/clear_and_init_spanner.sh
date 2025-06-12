#!/bin/bash

set -e

#
# NOTE it expects your gcloud config is set to the correct project and instance
#

show_usage() {
  echo "usage: $0 [options]"
  echo ""
  echo "Options:"
  echo " -h, --help               display this help message and exit"
  echo " -i, --instance INSTANCE  spanner instance name that are created on your G-Cloud"
  echo " -d, --database DATABASE  database name that will be created on your spanner instance"
}

parse_argv() {
  # default name of instance and database
  INSTANCE="pagoda"
  DATABASE="pagoda"

  while (( "$#" )); do
    case "$1" in
      -h|--help)
        show_usage
        exit 0
        ;;
      -i|--instance)
        INSTANCE=$2
        shift 2
        ;;
      -d|--database)
        DATABASE=$2
        shift 2
        ;;
      --) # end argument parsing
        shift
        break
        ;;
      -*|--*=)
        echo "Error: Unsupported flag ($1) is specified" >&2
        exit 1
        ;;
      *)
        ;;
    esac
  done
}

# Parse command-line arguments
parse_argv $*

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

echo "Database initialization completed successfully."
