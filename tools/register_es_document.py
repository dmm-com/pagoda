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


def register_entries(es):
    total_count = Entry.objects.filter(is_active=True).count()
    current_index = 1
    for entry in Entry.objects.filter(is_active=True):
        sys.stdout.write('\rRegister entry: (%6d/%6d)' % (current_index, total_count))

        entry.register_es(es, skip_refresh=True)

        current_index += 1

    es.indices.refresh(index=ES_INDEX)


if __name__ == "__main__":
    es = ESS()

    # clear previous index
    es.indices.delete(index=ES_INDEX, ignore=[400, 404])

    # create a new index with mapping
    es.recreate_index()

    register_entries(es)
