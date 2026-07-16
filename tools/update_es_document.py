import os
import sys
from optparse import OptionParser, Values

import configurations

# append airone directory to the default path
sys.path.append("./")

# prepare to load the data models of AirOne
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "airone.settings")
os.environ.setdefault("DJANGO_CONFIGURATION", "Dev")

# load AirOne application
configurations.setup()

from multidb.pinning import use_primary_db  # NOQA

from entity.models import Entity  # NOQA
from job.models import Job  # NOQA


def update_es_document(entities: list[str]) -> None:
    # Pin DB access to the primary. Outside of an HTTP request there is no
    # PinningRouterMiddleware to pin the thread after a write, so the Job row
    # created below would otherwise be read from a lagging replica and raise
    # Job.DoesNotExist when the synchronous task looks it up.
    with use_primary_db:
        target_entity = Entity.objects.filter(is_active=True)
        if entities:
            target_entity = target_entity.filter(name__in=entities)

        for entity in target_entity:
            Job.new_update_documents(entity).run(will_delay=False)


def get_options() -> tuple[Values, list[str]]:
    parser = OptionParser(usage="%prog [options] [target-Entities]")

    return parser.parse_args()


if __name__ == "__main__":
    (option, entities) = get_options()

    update_es_document(entities)
