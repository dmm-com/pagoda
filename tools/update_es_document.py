import django
import os
import sys
from optparse import OptionParser

# append airone directory to the default path
sys.path.append("./")

# prepare to load the data models of AirOne
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "airone.settings")

# load AirOne application
django.setup()

from airone.lib.elasticsearch import ESS # NOQA
from entry.models import Entry # NOQA
from django.db.models import Q # NOQA

ES_INDEX = django.conf.settings.ES_CONFIG['INDEX']


def register_documents(es, es_index, target_entities=None):
    db_query = Q(is_active=True)
    if target_entities:
        db_query = Q(db_query, Q(schema__name__in=target_entities))

    current_index = 1
    total_count = Entry.objects.filter(db_query).count()
    for entry in Entry.objects.filter(db_query):
        sys.stdout.write('\rRegister entry: (%6d/%6d)' % (current_index, total_count))

        entry.register_es(es, skip_refresh=True)

        current_index += 1

    es.indices.refresh(index=es_index)


def delete_unnecessary_documents(es, es_index):
    query = {
        'query': {
            'match_all': {}
        }
    }
    res = es.search(body=query)
    if 'status' in res and res['status'] == 404:
        raise('Failed to get entries')

    es_entry_ids = [int(x['_id']) for x in res['hits']['hits']]
    airone_entry_ids = Entry.objects.filter(is_active=True).values_list('id', flat=True)

    # delete documents that have been deleted already
    for entry_id in (set(es_entry_ids) - set(airone_entry_ids)):
        es.delete(doc_type='entry', id=entry_id, ignore=[404])

    es.indices.refresh(index=es_index)


def get_options():
    parser = OptionParser(usage="%prog [options] [target-Entities]")

    return parser.parse_args()


if __name__ == "__main__":
    (option, entities) = get_options()

    es = ESS()

    # register all entries to Elasticsearch
    register_documents(es, ES_INDEX, entities)

    # delete document which are already exists in AirOne
    delete_unnecessary_documents(es, ES_INDEX)
