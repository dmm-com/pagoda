#!/bin/bash

parse_argv() {
  if [ $# -ne 1 ]; then
    echo "usage: $0 <elasticsearch node address - where this script gets index data from>"
    echo "environment variables:"
    echo "  - ES_PORT: TCP port number to access to elasticsearch (current: ${ES_PORT:-9200})"
    exit 1
  fi

  ES_HOST=$1
  ES_PORT=${ES_PORT:-9200}
}

sync_es_index() {
  ES_HOST_CURR=$(python3 -c "from airone import settings; print(settings.ES_CONFIG['NODES'][0])")
  ES_INDEX=$(python3 -c "from airone import settings; print(settings.ES_CONFIG['INDEX'])")

  # wait until elasticsearch service would be available
  while ! nc -z ${ES_HOST_CURR/:/ }; do
    sleep 1
  done

  # clearup current ES and recreate index
  cat <<EOS | python3 manage.py shell
from airone.lib.elasticsearch import ESS

es = ESS()
es.indices.delete(index="${ES_INDEX}", ignore=[400, 404])
es.recreate_index()
EOS

  # sync elasticsearch index with specified node's data
  elasticdump --input=http://${ES_HOST}:${ES_PORT}/${ES_INDEX} \
              --output=http://${ES_HOST_CURR}/${ES_INDEX} \
              --limit=${ES_DUMP_MAXIMUM_NUMBER_OF_OBJECTS_PER_OPERATION:-500}
}

main() {
  parse_argv $*
  sync_es_index
}

main $*
