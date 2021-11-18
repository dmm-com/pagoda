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


def register_entries(es, target_entities=None):
    db_query = Q(is_active=True)
    if target_entities:
        db_query = Q(db_query, Q(schema__name__in=target_entities))

    current_index = 1
    total_count = Entry.objects.filter(db_query).count()
    for entry in Entry.objects.filter(db_query):
        sys.stdout.write('\rRegister entry: (%6d/%6d)' % (current_index, total_count))

        entry.register_es(es, skip_refresh=True)

        current_index += 1

    es.indices.refresh(index=ES_INDEX)


def get_options():
    parser = OptionParser(usage="%prog [options] [target-Entities]")

    return parser.parse_args()


if __name__ == "__main__":
    (option, entities) = get_options()

    es = ESS()

    # clear previous index
    es.indices.delete(index=ES_INDEX, ignore=[400, 404])

    # create a new index with mapping
    es.recreate_index()

    register_entries(es, entities)
