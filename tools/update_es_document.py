import django
import os
import sys

# append airone directory to the default path
sys.path.append("./")

# prepare to load the data models of AirOne
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "airone.settings")

# load AirOne application
django.setup()

from entry.models import Entry # NOQA
from airone.lib.elasticsearch import ESS # NOQA

ES_INDEX = django.conf.settings.ES_CONFIG['INDEX']


def register_documents(es, es_index):
    total_count = Entry.objects.filter(is_active=True).count()
    current_index = 1
    for entry in Entry.objects.filter(is_active=True):
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


if __name__ == "__main__":
    es = ESS()

    # register all entries to Elasticsearch
    register_documents(es, ES_INDEX)

    # delete document which are already exists in AirOne
    delete_unnecessary_documents(es, ES_INDEX)
